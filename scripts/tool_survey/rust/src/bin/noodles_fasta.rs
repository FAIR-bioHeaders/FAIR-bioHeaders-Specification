// Read a FASTA file with noodles-fasta and print each record.
use std::{env, fs::File, io::BufReader, process};

fn main() {
    let path = env::args().nth(1).expect("usage: noodles_fasta FILE");
    let mut reader = noodles_fasta::io::Reader::new(BufReader::new(File::open(path).unwrap()));
    for result in reader.records() {
        match result {
            Ok(record) => {
                let name = String::from_utf8_lossy(record.name());
                let seq = String::from_utf8_lossy(record.sequence().as_ref());
                println!(">{name}\n{seq}");
            }
            Err(e) => {
                eprintln!("error: {e}");
                process::exit(1);
            }
        }
    }
}
