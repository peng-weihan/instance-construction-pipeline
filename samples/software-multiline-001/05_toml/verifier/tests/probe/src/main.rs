use std::io::{self, BufRead};
use serde_json::{Value, json};
fn run(r: Value) -> Value {
    let op = r["op"].as_str().unwrap();
    if op == "serialize" {
        let value: toml::Value = serde_json::from_value(r["value"].clone()).unwrap();
        return match toml::to_string(&value) {
            Ok(text) => json!({"ok":true,"text":text}),
            Err(e) => json!({"ok":false,"error":e.to_string()}),
        };
    }
    let input = r["text"].as_str().unwrap();
    let parsed = toml::from_str::<toml::Value>(input);
    if op == "diagnostic" {
        return match parsed {
            Ok(v) => json!({"ok":true,"value":v}),
            Err(e) => json!({"ok":false,"message":e.message(),"span":e.span().map(|s|vec![s.start,s.end])}),
        };
    }
    let semantic = match parsed { Ok(v)=>v, Err(e)=>return json!({"ok":false,"error":e.to_string()}) };
    let mut doc = match input.parse::<toml_edit::DocumentMut>() {
        Ok(d)=>d, Err(e)=>return json!({"ok":false,"edit_error":e.to_string()})
    };
    if op == "edit" {
        for change in r["changes"].as_array().unwrap() {
            let mut item = doc.as_item_mut();
            for part in change["path"].as_array().unwrap() {
                item = if let Some(s)=part.as_str() { &mut item[s] } else { &mut item[part.as_u64().unwrap() as usize] };
            }
            let wrapper = json!({"replacement":change["value"]});
            let mut replacement = toml_edit::ser::to_document(&wrapper).unwrap();
            *item = replacement.remove("replacement").unwrap();
        }
    }
    let text = doc.to_string();
    let reparsed = toml::from_str::<toml::Value>(&text);
    match reparsed {
        Ok(v) => json!({"ok":true,"original":semantic,"value":v,"text":text}),
        Err(e)=>json!({"ok":false,"generated_error":e.to_string(),"text":text}),
    }
}
fn main() {
    for line in io::stdin().lock().lines() {
        let line=line.unwrap();
        let result=run(serde_json::from_str(&line).unwrap());
        println!("{}",result);
    }
}
