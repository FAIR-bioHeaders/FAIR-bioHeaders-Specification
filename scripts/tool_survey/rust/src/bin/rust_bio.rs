// Read a FASTA file with rust-bio and print each record.
use bio::io::fasta;
use std::{env, process};

fn main() {
    let path = env::args().nth(1).expect("usage: rust_bio FILE");
    let reader = fasta::Reader::from_file(path).unwrap();
    for result in reader.records() {
        match result {
            Ok(record) => println!(">{}\n{}", record.id(), String::from_utf8_lossy(record.seq())),
            Err(e) => {
                eprintln!("error: {e}");
                process::exit(1);
            }
        }
    }
}
