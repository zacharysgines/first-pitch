required_packages <- c("baseballr", "jsonlite")
missing_packages <- required_packages[!vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)]

if (length(missing_packages) > 0) {
  install.packages(missing_packages)
}

library(baseballr)
library(jsonlite)

get_script_dir <- function() {
  file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)

  if (length(file_arg) > 0) {
    return(dirname(normalizePath(sub("^--file=", "", file_arg[[1]]))))
  }

  getwd()
}

fangraphs_ip_to_decimal <- function(ip_value) {
  if (is.na(ip_value)) {
    return(NA_real_)
  }

  whole_innings <- floor(ip_value)
  partial <- round((ip_value - whole_innings) * 10)

  if (partial == 1) {
    return(whole_innings + (1 / 3))
  }

  if (partial == 2) {
    return(whole_innings + (2 / 3))
  }

  whole_innings
}

season <- as.integer(format(Sys.Date(), "%Y"))

fg_pitchers <- fg_pitcher_leaders(
  startseason = season,
  endseason = season,
  qual = 0
)

required_columns <- c("xMLBAMID", "PlayerName", "team_name_abb", "IP", "WAR")
missing_columns <- setdiff(required_columns, names(fg_pitchers))

if (length(missing_columns) > 0) {
  stop(
    paste(
      "FanGraphs response is missing expected column(s):",
      paste(missing_columns, collapse = ", ")
    )
  )
}

pitcher_war <- fg_pitchers[!is.na(fg_pitchers$xMLBAMID), required_columns]
pitcher_war$xMLBAMID <- as.character(as.integer(pitcher_war$xMLBAMID))
pitcher_war$PlayerName <- as.character(pitcher_war$PlayerName)
pitcher_war$team_name_abb <- as.character(pitcher_war$team_name_abb)
pitcher_war$IP <- round(vapply(as.numeric(pitcher_war$IP), fangraphs_ip_to_decimal, numeric(1)), 1)
pitcher_war$WAR <- round(as.numeric(pitcher_war$WAR), 1)

war_lookup <- setNames(
  lapply(seq_len(nrow(pitcher_war)), function(i) {
    list(
      Name = pitcher_war$PlayerName[[i]],
      Team = pitcher_war$team_name_abb[[i]],
      IP = pitcher_war$IP[[i]],
      WAR = pitcher_war$WAR[[i]]
    )
  }),
  pitcher_war$xMLBAMID
)

output_file <- file.path(get_script_dir(), "war_lookup.json")
metadata <- setNames(
  list(list(last_updated = as.character(Sys.Date()))),
  "_metadata"
)
war_output <- c(metadata, war_lookup)

write_json(war_output, output_file, auto_unbox = TRUE, pretty = TRUE, null = "null")

cat("Saved", length(war_lookup), "pitcher WAR records to", output_file, "\n")
