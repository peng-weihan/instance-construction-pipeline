package submission;
import ai.abstraction.WorkerRush;
import ai.core.AI;
import rts.units.UnitTypeTable;
/** Starter delegates to a fixed rush; replace with a stateful strategy. */
public class FrontierAI extends WorkerRush {
    private final UnitTypeTable table;
    public FrontierAI(UnitTypeTable utt) { super(utt); table=utt; }
    @Override public AI clone() { return new FrontierAI(table); }
}
