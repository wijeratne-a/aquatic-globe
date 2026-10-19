#!/usr/bin/env Rscript
# Download AquaMaps SQLite via aquamapsdata (optional convenience wrapper).

.libPaths(c(Sys.getenv("R_LIBS_USER", "/home/ubuntu/R/library"), .libPaths()))

if (!requireNamespace("aquamapsdata", quietly = TRUE)) {
  stop(
    "Install aquamapsdata first, e.g.\n",
    "  remotes::install_github('raquamaps/aquamapsdata', lib=Sys.getenv('R_LIBS_USER'))"
  )
}

library(aquamapsdata)

target <- file.path("/workspace/data", "am.db")
dir.create(dirname(target), recursive = TRUE, showWarnings = FALSE)

if (!file.exists(target)) {
  message("Downloading AquaMaps database (~2 GB compressed)...")
  download_db()
  src <- am_db_sqlite()
  if (normalizePath(src) != normalizePath(target)) {
    message("Copying ", src, " -> ", target)
    file.copy(src, target)
  }
} else {
  message("Database already present at ", target)
}

message("Done: ", target)
