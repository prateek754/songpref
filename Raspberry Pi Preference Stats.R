################################
## A cost-effective Raspberry pi based operant playback setup to evaluate auditory preferences in songbirds
## The script contains code for data cleaning and analysis of the data collected from the operant playback setup

## Before running the code, make sure the data files are in the correct folder

## The data files should be in the "data" folder in the same working directory as this script

## By Prateek K. Sahu
################################

############################################

# 1. The first section contains code for data cleaning 
# If you directly want to analyze the data, you can skip this section and go to line 88

###########################################

## Load libraries

library(data.table) #install and load the package "data.table" for data manipulation

# Below function takes two CSV files and an ID as input, processes the data, and returns a combined data table
# The function reads the CSV files, formats the timestamp, filters out interrupted trials, 
# assigns species and choice based on perch_number, selects relevant columns, adds an ID column, and combines the datasets.

# If you want to include the interrupted trials, you can comment out the lines that filter them out.
# The A1 and A2 assumes A and B condition, respectively. Be careful to use the correct file names and paths.

process_bird_data <- function(file1, file2, id) {
  # Read CSV files
  A1 <- fread(file1)
  A2 <- fread(file2)
  
  # Format timestamp
  A1[, timestamp := format(timestamp, "%H:%M:%OS")]
  A2[, timestamp := format(timestamp, "%H:%M:%OS")]
  
  # Filter out interrupted trials
  A1 <- A1[interrupted_trial == FALSE]
  A2 <- A2[interrupted_trial == FALSE]
  
  # Assign species and choice based on perch_number
  A1[, species := fifelse(perch_number == 2, "BCCH", "WTSP")]
  A1[, choice := fifelse(perch_number == 2, "1", "0")]
  
  A2[, species := fifelse(perch_number == 1, "BCCH", "WTSP")]
  A2[, choice := fifelse(perch_number == 1, "1", "0")]
  
  # Select relevant columns
  newA1 <- A1[, .(timestamp, species, choice,visit_count,sound_file, experimental_condition)]
  newA2 <- A2[, .(timestamp, species, choice,visit_count,sound_file, experimental_condition)]
  
  # Add ID column
  newA1[, ID := factor(id)]
  newA2[, ID := factor(id)]
  
  # Combine datasets
  A <- rbind(newA2, newA1)
  
  return(A)
}

# Running the function for each bird and combining the results

A <- process_bird_data("data/bird_G55M9am_20250310_conditionBm.csv",
                       "data/bird_G55M1pm_20250310_conditionA.csv",
                       "G55M")
B <- process_bird_data("data/bird_G600M9am_20250312_conditionB.csv",
                       "data/bird_G600M1pm_20250312_conditionA.csv",
                       "G600M")
C <- process_bird_data("data/bird_G683M1pm_20250311_conditionB.csv",
                       "data/bird_G683A9am_20250311_conditionA.csv",
                       "G683M")
D <- process_bird_data("data/bird_G675M12noon_20250313_conditionB.csv",
                       "data/bird_G675M9am_20250313_conditionA.csv",
                       "G675M")

Allbirds <- rbind(A,B,C,D)

# save the combined data to a CSV file
write.csv(Allbirds, "data/Allbirds.csv", row.names = FALSE)

# Preference index was calculated manually from the data files without interrupted trials
# as following: preference index = perch visits to conspecific stimuli / (perch visits to conspecific stimuli + perch visits to heterospecific stimuli)
############################################

# 2. The second section contains code for analyzing the data

###########################################
# Install and load the required packages as below
library(ggplot2)
library(data.table)
library(rstanarm)
library(bayesplot)
library(loo)

# Load the data
pref_data <- fread("data/Allbirds.csv")
## pref_data <- fread("data/Allbirdswithit.csv")  # Uncomment this line if you want to include interrupted trials
# Convert the timestamp to a more manageable format
pref_data[, TimeOfDay := {
  time_parts <- strsplit(timestamp, ":")
  hour <- as.numeric(sapply(time_parts, function(x) x[1]))
  minute <- as.numeric(sapply(time_parts, function(x) x[2]))
  second <- as.numeric(sapply(time_parts, function(x) x[3]))
  hour + minute/60 + second/3600
}]

# Convert columns to factors
pref_data$ID <- factor(pref_data$ID)
pref_data$experimental_condition <- factor(pref_data$experimental_condition)
pref_data$choice <- factor(pref_data$choice)
pref_data$sound_file <- factor(pref_data$sound_file)
pref_data$species <- factor(pref_data$species)
pref_data[, time_std := scale(TimeOfDay)[,1]] # scale the time of day for standardization

## Bayesian GLMM analysis; only one model included but can compare multiple models with loo 

# Model: Model with random intercepts and random slopes 
model5 <- stan_glmer(
  choice ~ 1 + time_std + experimental_condition + (1 + time_std|ID),
  family = binomial(link = "logit"),
  data = pref_data,
  prior = normal(0, 1),
  prior_intercept = normal(0, 1.5),
  prior_covariance = decov(shape = 2, scale = 2.5),
  chains = 4,
  iter = 2000,
  warmup = 1000,
  seed = 756,
  adapt_delta = 0.95
)

# Model summary
print(summary(model5))

# Posterior predictive checks
pp_check(model5, nreps = 50)

# Extract fixed effects
fixed_effectsmodel <- fixef(model5)
fixed_effectsmodel

# Extract random effects for birds
bird_effects <- ranef(model5)$ID
bird_effects

# Posterior intervals

posterior_interval(model5, prob = 0.90)

# Extract posterior samples
posterior_samples <- as.matrix(model5)
fixed_effects <- posterior_samples[, 1:3]
time_seq <- seq(min(pref_data$time_std), max(pref_data$time_std), length.out = 100)


# Calculate overall predicted probabilities across the time sequence
intercept_samples <- posterior_samples[, "(Intercept)"]
time_samples <- posterior_samples[, "time_std"]
overall_prob_samples <- sapply(time_seq, function(t) {
  plogis(intercept_samples + time_samples * t)
})

# Calculate mean and 90% credible intervals for overall predicted probabilities

mean_overall_prob <- mean(overall_prob_samples) * 100
overall_ci <- quantile(overall_prob_samples, c(0.05, 0.95)) * 100
round(mean_overall_prob, 1)
round(overall_ci, 1)

# Create a new data frame for predictions
new_data <- expand.grid(
  ID = unique(pref_data$ID),
  time_std = time_seq,
  experimental_condition = "A"  # change this to B if needed but both are included generally
)
# Generate predictions
predicted_probs <- posterior_epred(model5, newdata = new_data)
new_data$predicted_prob <- colMeans(predicted_probs)

# Plot the predicted probabilities for each bird 

ggplot(new_data, aes(x = time_std, y = predicted_prob, color = ID, group = ID)) +
  geom_line(linewidth=1,alpha = 0.7) +
  geom_hline(yintercept = 0.5, linetype = "dotted", color = "black")+
  scale_y_continuous(limits = c(0, 1), breaks = seq(0.1, 0.9, 0.2)) +
  labs(x = "Standardized time", y = "Predicted probability of choice")+
  theme_minimal() +
  theme(axis.line.y = element_line(color = "black"),
        axis.line.x = element_blank(),
        axis.ticks.y = element_line(color = "black"),
        panel.grid = element_blank())

## 90% CIs for each bird overall throughout the time point for Figure 2
dtci <- as.data.table(new_data)
dtci[, `:=`(
  lower_ci = apply(predicted_probs, 2, quantile, probs = 0.05),
  upper_ci = apply(predicted_probs, 2, quantile, probs = 0.95)
)]
bird_ci <- dtci[, .(
     overall_lower = min(lower_ci),
     overall_upper = max(upper_ci)
   ), by = ID][, ci_90 := paste0("90% CI: ", round(overall_lower, 3), "-", round(overall_upper, 3))]

print(bird_ci[, list(ID, ci_90)])

## for an overall trend of dynamics of preference score across time, we can calculate the mean probability of choice at the start and end of the experiment
## For "Results section"
# Extract fixed effects for the model
fixed_effects <- fixef(model5)
intercept <- fixed_effects["(Intercept)"]
time_effect <- fixed_effects["time_std"]


# Extract the start and end times of the experiment and corresponding posterior samples
start_time <- min(pref_data$time_std)
end_time <- max(pref_data$time_std)
posterior_samples <- as.matrix(model5)
intercept_samples <- posterior_samples[, "(Intercept)"]
time_samples <- posterior_samples[, "time_std"]

# Mean and 90% CI at Start of experiment 
start_intercept_samples <- intercept_samples + (time_samples * start_time)
start_prob_samples <- plogis(start_intercept_samples)
start_prob <- mean(start_prob_samples) * 100
start_ci <- quantile(start_prob_samples, c(0.05, 0.95)) * 100

# Mean and 90% CI at End of experiment  
end_intercept_samples <- intercept_samples + (time_samples * end_time)
end_prob_samples <- plogis(end_intercept_samples)
end_prob <- mean(end_prob_samples) * 100
end_ci <- quantile(end_prob_samples, c(0.05, 0.95)) * 100

data.frame(
  timepoint = c("start", "end"),
  probability = round(c(start_prob, end_prob), 1),
  ci_lower = round(c(start_ci[1], end_ci[1]), 1),
  ci_upper = round(c(start_ci[2], end_ci[2]), 1)
)


###### Individual baseline and final choice probabilities for each bird

dt <- as.data.table(new_data)
dt[, c("lower_ci", "upper_ci") := list(
  apply(predicted_probs, 2, quantile, probs = 0.05),
  apply(predicted_probs, 2, quantile, probs = 0.95)
)]

g683_data <- dt[ID == "G683M"]    # change "G683M" to the ID of the bird you want to analyze
baseline <- g683_data[time_std == min(time_std)]
final <- g683_data[time_std == max(time_std)]

# Calculate baseline and final choice probabilities
baseline_pct <- round(baseline$predicted_prob * 100)
baseline_ci <- round(c(baseline$lower_ci, baseline$upper_ci) * 100)
final_pct <- round(final$predicted_prob * 100) 
final_ci <- round(c(final$lower_ci, final$upper_ci) * 100)

