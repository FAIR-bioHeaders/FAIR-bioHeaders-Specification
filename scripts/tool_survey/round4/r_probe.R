# Usage: Rscript r_probe.R METHOD FILE
# Prints the record count, then name<TAB>length<TAB>md5(upper-cased sequence) per record.
# METHOD: biostrings (readDNAStringSet), biostrings_index (fasta.index, then
# readDNAStringSet on the index), seqinr (read.fasta), ape_FASTA (read.FASTA),
# ape_dna (read.dna(format = "fasta")).
suppressPackageStartupMessages({library(Biostrings); library(seqinr); library(ape)})
a <- commandArgs(TRUE); m <- a[1]; f <- a[2]
md5 <- function(s) { t <- tempfile(); writeChar(toupper(s), t, eos = NULL); r <- unname(tools::md5sum(t)); unlink(t); r }
emit <- function(n, s) { cat(sprintf("%d records\n", length(s))); for (i in seq_along(s)) cat(sprintf("%s\t%d\t%s\n", n[i], nchar(s[i]), md5(s[i]))) }
nm1 <- function(x) sub(" .*", "", x)
withCallingHandlers({
if (m == "biostrings") { x <- readDNAStringSet(f); emit(nm1(names(x)), as.character(x)) }
if (m == "biostrings_index") { x <- readDNAStringSet(fasta.index(f)); emit(nm1(names(x)), as.character(x)) }
if (m == "seqinr") { x <- read.fasta(f, seqtype = "DNA", as.string = TRUE, forceDNAtolower = FALSE); emit(names(x), unlist(lapply(x, function(y) y[1]))) }
if (m == "ape_FASTA") { x <- read.FASTA(f); emit(nm1(names(x)), sapply(as.character(x), paste, collapse = "")) }
if (m == "ape_dna") {
  x <- read.dna(f, format = "fasta")
  if (is.matrix(x)) { n <- rownames(x); s <- apply(as.character(x), 1, paste, collapse = "") } else { n <- names(x); s <- sapply(as.character(x), paste, collapse = "") }
  emit(nm1(n), s)
}
}, error = function(e) { message("Error: ", conditionMessage(e)); quit(status = 1) })
