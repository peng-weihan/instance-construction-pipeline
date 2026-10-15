// Task-specific harness, using the genuine DataFusion SortExec/TopK operators.
// New harness code: MIT OR Apache-2.0, same dual-license permission as author material.
use std::io::{self, BufRead, Write};
use std::sync::Arc;
use arrow::array::{Array, ArrayRef, Int64Array, UInt64Array, StringArray};
use arrow::compute::SortOptions;
use arrow::datatypes::{DataType, Field, Schema};
use arrow::record_batch::RecordBatch;
use datafusion_execution::TaskContext;
use datafusion_physical_expr::{LexOrdering, PhysicalSortExpr, expressions::col};
use datafusion_physical_plan::{ExecutionPlan, collect};
use datafusion_physical_plan::sorts::{sort::SortExec, sort_preserving_merge::SortPreservingMergeExec};
use datafusion_physical_plan::test::TestMemoryExec;
use serde_json::{Value, json};
#[tokio::main(flavor="current_thread")]
async fn main() {
    let mut input=io::stdin().lock();let mut line=String::new();input.read_line(&mut line).unwrap();
    let spec:Value=serde_json::from_str(&line).unwrap();
    let n=spec["rows"].as_u64().unwrap() as usize;
    let partitions=spec["partitions"].as_u64().unwrap() as usize;
    let batch_size=spec["batch_size"].as_u64().unwrap() as usize;
    let width=spec["payload_width"].as_u64().unwrap() as usize;
    let seed=spec["seed"].as_u64().unwrap();
    let null_every=spec["null_every"].as_u64().unwrap();
    let tag_null_every=spec["tag_null_every"].as_u64().unwrap();
    let descending=spec["descending"].as_bool().unwrap();
    let nulls_first=spec["nulls_first"].as_bool().unwrap();
    let prefix=spec["ordered_prefix"].as_bool().unwrap();
    let fetch=spec["k"].as_u64().map(|v|v as usize);
    let schema=Arc::new(Schema::new(vec![Field::new("id",DataType::UInt64,false),Field::new("key",DataType::Int64,true),Field::new("tag",DataType::Utf8,true),Field::new("payload",DataType::Utf8,false)]));
    let mut parts=Vec::new();
    for partition in 0..partitions {
        let ids:Vec<u64>=(partition..n).step_by(partitions).map(|i|i as u64).collect();
        let mut batches=Vec::new();
        for ids in ids.chunks(batch_size) {
            let mut keys=Vec::new();let mut tags=Vec::new();let mut payload=Vec::new();
            for &i in ids {
                let x=i.wrapping_mul(6364136223846793005).wrapping_add(seed);
                keys.push(if null_every>0 && i%null_every==0 {None} else if prefix {Some((i/512) as i64)} else {Some(((x>>17)%97) as i64-48)});
                tags.push(if tag_null_every>0 && i%tag_null_every==0 {None} else {Some(format!("t{:04}-{}",x%1009,if x%3==0 {"中"} else {"z"}))});
                payload.push(format!("p{i:016x}:{}","z".repeat(width)));
            }
            batches.push(RecordBatch::try_new(schema.clone(),vec![Arc::new(UInt64Array::from(ids.to_vec())) as ArrayRef,Arc::new(Int64Array::from(keys)),Arc::new(StringArray::from(tags)),Arc::new(StringArray::from(payload))]).unwrap());
        }
        parts.push(batches);
    }
    let first=PhysicalSortExpr::new(col("key",&schema).unwrap(),SortOptions{descending,nulls_first});
    let ordering=LexOrdering::new([first.clone(),PhysicalSortExpr::new(col("tag",&schema).unwrap(),SortOptions{descending:!descending,nulls_first:!nulls_first}),PhysicalSortExpr::new(col("id",&schema).unwrap(),SortOptions{descending:false,nulls_first:false})]).unwrap();
    let mut memory=TestMemoryExec::try_new(&parts,schema,None).unwrap();
    if prefix {memory=memory.try_with_sort_information(vec![LexOrdering::new([first]).unwrap()]).unwrap();}
    let source:Arc<dyn ExecutionPlan>=Arc::new(memory);
    let sorted:Arc<dyn ExecutionPlan>=Arc::new(SortExec::new(ordering.clone(),source).with_fetch(fetch).with_preserve_partitioning(true));
    let plan:Arc<dyn ExecutionPlan>=Arc::new(SortPreservingMergeExec::new(ordering,sorted).with_fetch(fetch));
    // Host timer starts after all generation/Arrow preparation/plan construction.
    println!("READY");io::stdout().flush().unwrap();line.clear();input.read_line(&mut line).unwrap();assert_eq!(line.trim(),"GO");drop(input);
    let batches=collect(plan,Arc::new(TaskContext::default())).await.unwrap();
    let mut rows=Vec::new();
    for b in batches {
        let id=b.column(0).as_any().downcast_ref::<UInt64Array>().unwrap();let key=b.column(1).as_any().downcast_ref::<Int64Array>().unwrap();
        let tag=b.column(2).as_any().downcast_ref::<StringArray>().unwrap();let payload=b.column(3).as_any().downcast_ref::<StringArray>().unwrap();
        for i in 0..b.num_rows() {rows.push(json!([id.value(i),if key.is_null(i){None}else{Some(key.value(i))},if tag.is_null(i){None}else{Some(tag.value(i))},payload.value(i)]));}
    }
    println!("{}",json!({"rows":rows}));
}
