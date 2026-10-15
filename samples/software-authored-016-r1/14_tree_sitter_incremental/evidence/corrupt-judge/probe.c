#include <tree_sitter/api.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
extern const TSLanguage *tree_sitter_python(void);
static uint32_t u(void) { unsigned char b[4]; if(fread(b,1,4,stdin)!=4) exit(3); return b[0]|b[1]<<8|b[2]<<16|b[3]<<24; }
static char *blob(uint32_t *n) { *n=u(); char *s=calloc(*n+1,1); if(fread(s,1,*n,stdin)!=*n)exit(3); return s; }
static TSPoint point(void) { TSPoint p; p.row=u(); p.column=u(); return p; }
static void ranges(TSParser *p) { uint32_t n=u(); TSRange *r=calloc(n?n:1,sizeof(TSRange)); for(unsigned i=0;i<n;i++){ r[i].start_point=point();r[i].end_point=point();r[i].start_byte=u();r[i].end_byte=u(); } if(!ts_parser_set_included_ranges(p,r,n))exit(4);free(r); }
static void node(TSNode n, unsigned depth, int changes) {
 TSPoint a=ts_node_start_point(n),b=ts_node_end_point(n);
 printf("%u %s %u %u %u %u %u %u %u %u %u %u %u",depth,ts_node_type(n),ts_node_is_named(n),ts_node_is_extra(n),ts_node_is_missing(n),ts_node_is_error(n),ts_node_has_error(n),ts_node_start_byte(n),ts_node_end_byte(n),a.row,a.column,b.row,b.column);
 if(changes)printf(" %u",ts_node_has_changes(n));puts("");
 for(unsigned i=0;i<ts_node_child_count(n);i++){
  const char *f=ts_node_field_name_for_child(n,i);printf("field %s\n",f?f:"-");node(ts_node_child(n,i),depth+1,changes);
 }
}
static void dump(const char *tag,TSTree *t,int changes){ printf("@%s\n",tag);node(ts_tree_root_node(t),0,changes);puts("@end"); }
static void named(TSNode n){ if(!ts_node_is_named(n))return; printf("(%s",ts_node_type(n));for(unsigned i=0;i<ts_node_named_child_count(n);i++){putchar(' ');named(ts_node_named_child(n,i));}putchar(')'); }
static void ir(TSTree *t){unsigned n;TSRange *r=ts_tree_included_ranges(t,&n);puts("@included");for(unsigned i=0;i<n;i++)printf("%u %u %u %u %u %u\n",r[i].start_byte,r[i].end_byte,r[i].start_point.row,r[i].start_point.column,r[i].end_point.row,r[i].end_point.column);puts("@end");free(r);}
int main(void){
 uint32_t enc=u(),size;TSInputEncoding encoding=enc==1?TSInputEncodingUTF16LE:enc==2?TSInputEncodingUTF16BE:TSInputEncodingUTF8;
 TSParser *p=ts_parser_new(),*fresh=ts_parser_new();if(!ts_parser_set_language(p,tree_sitter_python())||!ts_parser_set_language(fresh,tree_sitter_python()))return 5;
 ranges(p);char *src=blob(&size);TSTree *t=ts_parser_parse_string_encoding(p,NULL,src,size,encoding);if(!t)return 6;
 dump("initial",t,0);puts("@sexp");named(ts_tree_root_node(t));puts("\n@end");
 uint32_t batches=u();
 for(unsigned k=0;k<batches;k++){
  TSTree *copy=ts_tree_copy(t);TSNode saved=ts_node_named_child(ts_tree_root_node(t),0);if(ts_node_is_null(saved))saved=ts_tree_root_node(t);
  unsigned edits=u();
  for(unsigned j=0;j<edits;j++){
   TSInputEdit e;e.start_byte=u();e.old_end_byte=u();e.new_end_byte=u();e.start_point=point();e.old_end_point=point();e.new_end_point=point();
   ts_tree_edit(t,&e);ts_node_edit(&saved,&e);free(src);src=blob(&size);
   dump("edited",t,1);dump("copy",copy,1);puts("@handle");node(saved,0,1);puts("@end");ir(t);
  }
  ranges(p);unsigned count;const TSRange *pr=ts_parser_included_ranges(p,&count);if(!ts_parser_set_included_ranges(fresh,pr,count))return 7;
  TSTree *next=ts_parser_parse_string_encoding(p,t,src,size,encoding),*full=ts_parser_parse_string_encoding(fresh,NULL,src,size,encoding);if(!next||!full)return 8;
  dump("parsed",next,0);dump("fresh",full,0);
  puts("@changed");unsigned n;TSRange *r=ts_tree_get_changed_ranges(t,next,&n);for(unsigned i=0;i<n;i++)printf("%u %u %u %u %u %u\n",r[i].start_byte,r[i].end_byte,r[i].start_point.row,r[i].start_point.column,r[i].end_point.row,r[i].end_point.column);puts("@end");free(r);
  ts_tree_delete(copy);ts_tree_delete(t);ts_tree_delete(full);t=next;
 }
 free(src);ts_tree_delete(t);ts_parser_delete(p);ts_parser_delete(fresh);return 0;
}
