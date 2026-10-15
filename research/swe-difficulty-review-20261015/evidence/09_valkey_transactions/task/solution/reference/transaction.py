"""Connection state and transaction admission, execution and durable publication."""
from resp import Error, Simple
from store import CommandError, validate

class Session:
    def __init__(self, ident):
        self.ident = ident
        self.queue = None
        self.dirty = False
        self.watches = {}

    def reset(self):
        self.queue = None
        self.dirty = False
        self.watches.clear()

class Engine:
    def __init__(self, store, journal):
        self.store, self.journal = store, journal

    def batch(self, commands, client_id):
        # All commands run without yielding to another connection. Runtime errors
        # are results; they neither roll back preceding commands nor stop EXEC.
        old_now = self.store.now
        self.store.changed = set()
        results = []
        for argv in commands:
            try:
                results.append(self.store.command(validate(argv), argv[1:], client_id))
            except CommandError as exc:
                results.append(Error(str(exc)))
        # An I/O failure is fatal. No client may observe unsynced state or reply.
        self.journal.commit(old_now)
        return results

    def execute(self, session, argv):
        try:
            cmd = validate(argv)
            if session.queue is not None and cmd in ('MULTI','WATCH','CLOCK','HELLO','QUIT'):
                raise CommandError('ERR command not allowed inside a transaction')
        except CommandError as exc:
            if session.queue is not None:
                session.dirty = True
            return Error(str(exc)), False
        if cmd == 'QUIT':
            session.reset()
            return Simple('OK'), True
        if cmd == 'MULTI':
            session.queue = []
            return Simple('OK'), False
        if cmd == 'WATCH':
            for key in argv[1:]:
                session.watches.setdefault(key, self.store.versions.get(key,0))
            return Simple('OK'), False
        if cmd == 'EXEC':
            if session.queue is None:
                return Error('ERR EXEC without MULTI'), False
            queue, dirty = session.queue, session.dirty
            stale = any(self.store.versions.get(k,0) != v for k,v in session.watches.items())
            session.reset()
            if dirty:
                return Error('EXECABORT Transaction discarded because of previous errors'), False
            if stale:
                return None, False
            return self.batch(queue, session.ident), False
        if cmd == 'DISCARD':
            if session.queue is None:
                return Error('ERR DISCARD without MULTI'), False
            session.reset()
            return Simple('OK'), False
        # UNWATCH, like ordinary commands, is queued in MULTI.
        if session.queue is not None:
            session.queue.append(argv)
            return Simple('QUEUED'), False
        if cmd == 'UNWATCH':
            session.watches.clear()
            return Simple('OK'), False
        return self.batch([argv], session.ident)[0], False
