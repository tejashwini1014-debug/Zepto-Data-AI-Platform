# Module 2 — Titanic Analytics and Predictive Modeling

## 1. Module Overview

This module implements a complete analytics and machine learning workflow using the Titanic dataset.

The workflow includes:

- Data loading and profiling
- Missing-value analysis and handling
- Univariate, bivariate, and multivariate analysis
- Exploratory standardization
- Stratified train/test splitting
- Training-only preprocessing using `ColumnTransformer` and `Pipeline`
- Classification using Logistic Regression, Decision Tree, and Random Forest
- Confusion matrices and ROC/AUC evaluation
- Class imbalance comparison using baseline, class weighting, and SMOTE
- Random Forest hyperparameter tuning using `GridSearchCV`
- Multivariate Linear Regression for fare prediction
- Residual analysis and heteroscedasticity check
- Final model comparison
- Saving and reloading the complete fitted machine learning pipeline

The raw Titanic dataset was loaded once using Seaborn and saved as `titanic.csv`.

The modeling notebook reads the saved CSV and does not call `sns.load_dataset("titanic")` again.

---

# Part A — Profiling, Cleaning, and Data Story

## 2. Task 1 — Data Loading and Profiling

The Titanic dataset was loaded once using:

```python
titanic = sns.load_dataset("titanic")
titanic.to_csv("titanic.csv", index=False)
```

The dataset was then loaded from the saved CSV file for all subsequent analysis.

The dataset contains 891 rows and 15 columns.

The following profiling information was generated:

- `df.info()`
- `df.describe()`
- `df.shape`
- Missing-value percentages for affected columns

### Dataset Shape

```text
Rows: 891
Columns: 15
```

### Columns With Missing Values

| Column | Missing Values | Missing Percentage |
|---|---:|---:|
| age | 177 | 19.8653% |
| embarked | 2 | 0.2245% |
| deck | 688 | 77.2166% |
| embark_town | 2 | 0.2245% |

The `age` column had a moderate amount of missing data, while `deck` had a very high percentage of missing values.

---

## 3. Task 2 — Missing-Value Handling

The following missing-value strategy was used based on the measured missing percentages.

### `age`

The `age` column had 19.8653% missing values.

Since the missing percentage was between 5% and 30%, the missing values were replaced using the median age.

Median imputation was selected because age contains numerical values and the median is less affected by extreme values.

### `embarked`

The `embarked` column had 0.2245% missing values.

Since the missing percentage was below 5%, the affected rows were removed.

### `embark_town`

The `embark_town` column also had 0.2245% missing values.

The affected rows were removed along with the corresponding `embarked` values.

### `deck`

The `deck` column had 77.2166% missing values.

Because the missing percentage was very high, the column was removed instead of performing large-scale imputation.

### Final Cleaning

After cleaning:

```text
Rows: 889
Columns: 14
Remaining missing values: 0
```

The cleaned dataset was used for the remaining exploratory analysis.

---

## 4. Task 3 — Univariate Analysis and Outlier Detection

Histograms and boxplots were created for `age` and `fare`.

### Age

The age distribution was visualized using a histogram.

A boxplot was also created to identify potential outliers.

Using the IQR method, 65 age observations were identified as potential outliers.

### Fare

The fare distribution was visualized using a histogram and boxplot.

Using the IQR method, 114 fare observations were identified as potential outliers.

### Fare Statistics

| Statistic | Value |
|---|---:|
| Mean | 32.0967 |
| Median | 14.4542 |
| Mode | 8.05 |
| Skewness | 4.8014 |

The fare distribution is strongly positively skewed because the mean is considerably higher than the median and the skewness value is positive.

The boxplot also shows several high-fare observations.

---

## 5. Task 4 — Survival Analysis and Correlation

Survival rates were calculated using boolean masking for:

- Survival rate by sex
- Survival rate by passenger class
- Survival rate by sex and passenger class

### Survival Rate by Sex

| Sex | Survival Rate |
|---|---:|
| Male | 18.89% |
| Female | 74.04% |

Female passengers had a higher survival rate than male passengers in this dataset.

### Survival Rate by Passenger Class

| Passenger Class | Survival Rate |
|---|---:|
| 1 | 62.62% |
| 2 | 47.28% |
| 3 | 24.24% |

The survival rate was highest for first-class passengers and lowest for third-class passengers.

### Survival Rate by Sex and Passenger Class

| Sex | Class | Survival Rate |
|---|---:|---:|
| Female | 1 | 96.74% |
| Female | 2 | 92.11% |
| Female | 3 | 50.00% |
| Male | 1 | 36.89% |
| Male | 2 | 15.74% |
| Male | 3 | 13.54% |

### Correlation Analysis

The correlation matrix was calculated using exactly these six columns:

- `survived`
- `pclass`
- `age`
- `sibsp`
- `parch`
- `fare`

The columns `adult_male` and `alone` were excluded.

A correlation heatmap was created using these six columns.

The two strongest absolute off-diagonal correlations were:

| Feature Pair | Correlation |
|---|---:|
| pclass — fare | -0.548193 |
| sibsp — parch | 0.414542 |

The negative correlation between `pclass` and `fare` indicates that lower passenger-class numbers, representing higher passenger classes, were generally associated with higher fares.

The positive correlation between `sibsp` and `parch` indicates that passengers with more siblings/spouses also tended to have more parents/children traveling with them.

---

## 6. Task 5 — Multivariate Analysis

Multiple multivariate visualizations were created to understand relationships between features and survival.

### Chart 1 — Survival by Passenger Class and Sex

The chart compares survival rates across passenger classes for male and female passengers.

Female passengers generally had higher survival rates than male passengers across all classes.

Survival was also generally higher in first class and lower in third class.

### Chart 2 — Age vs Fare by Survival

The relationship between age and fare was visualized using survival status.

Most passengers were concentrated at relatively lower fares, while a smaller number of passengers had very high fares.

Survival patterns varied across different ages and fare values.

### Chart 3 — Fare by Passenger Class and Survival

Fare distributions were compared across passenger classes and survival status.

First-class passengers generally paid higher fares than passengers in second and third class.

Several high-fare observations were visible, particularly among first-class passengers.

### Chart 4 — Age vs Passenger Class by Survival

Age and passenger class were visualized together using survival status.

The age distribution differed across passenger classes, and survival patterns also varied between survivors and non-survivors within the classes.

---

## 7. Task 6 — Exploratory Standardization

Standardization was applied to `age` and `fare` on the full cleaned DataFrame for exploratory analysis.

### Before Standardization

| Feature | Mean | Standard Deviation |
|---|---:|---:|
| age | 29.3152 | 12.9849 |
| fare | 32.0967 | 49.6975 |

### After Standardization

| Feature | Mean | Standard Deviation |
|---|---:|---:|
| age | approximately 0 | approximately 1 |
| fare | approximately 0 | approximately 1 |

The standardized features had means close to 0 and standard deviations close to 1.

This standardization was used only for exploratory analysis and was not used directly for model training.

---

# Part B — Predictive Modeling

## 8. Task 7 — Stratified Train/Test Split

The cleaned dataset was divided into training and testing sets using an 80/20 stratified split.

```text
Training set: 711 rows
Testing set: 178 rows
```

The target variable was `survived`.

Stratification was used so that the proportion of survived and not-survived passengers remained similar in both the training and testing sets.

The class proportions were approximately:

```text
Training:
Not Survived = 61.74%
Survived     = 38.26%

Testing:
Not Survived = 61.80%
Survived     = 38.20%
```

---

## 9. Task 8 — Data Preprocessing

Preprocessing was performed using a `ColumnTransformer` and `Pipeline`.

### Numerical Features

The numerical features were:

- `pclass`
- `age`
- `sibsp`
- `parch`
- `fare`

For numerical features:

- Missing values were handled using median imputation.
- Features were standardized using `StandardScaler`.

### Categorical Features

The categorical features were:

- `sex`
- `embarked`

For categorical features:

- Missing values were handled using the most frequent value.
- Categorical values were converted into numerical form using `OneHotEncoder`.
- `handle_unknown="ignore"` was used to handle unseen categories.

The preprocessing steps were fitted only on the training data and then applied to the test data.

This prevents information from the test set from being used during training.

The redundant or derived columns `alive`, `class`, `who`, `adult_male`, and `alone` were not used as model features.

---

## 10. Task 9 — Classification Models

Three classification models were trained using the same training and testing split and preprocessing pipeline:

1. Logistic Regression
2. Decision Tree
3. Random Forest

The preprocessing and classifier were combined into complete pipelines so that the same transformations were applied consistently.

### Initial Random Forest

The initial Random Forest was configured as:

```python
RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    oob_score=True
)
```

The initial Random Forest OOB score was:

```text
0.8017
```

### Decision Tree Visualization

The trained Decision Tree was visualized using `plot_tree()` with feature names and class labels:

- `Not Survived`
- `Survived`

The visualization was limited to the first three levels of the tree for better readability.

---

## 11. Task 10 — Model Evaluation and Comparison

The classification models were evaluated using:

- Confusion Matrix
- Accuracy
- Precision
- Recall
- F1-score
- ROC curve
- ROC-AUC

### Classification Model Comparison

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.8090 | 0.7833 | 0.6912 | 0.7344 | 0.8610 |
| Decision Tree | 0.7640 | 0.7600 | 0.5588 | 0.6441 | 0.8374 |
| Random Forest | 0.8202 | 0.7812 | 0.7353 | 0.7576 | 0.8179 |

### Confusion Matrices

#### Logistic Regression

```text
TN = 97
FP = 13
FN = 21
TP = 47
```

#### Decision Tree

```text
TN = 98
FP = 12
FN = 30
TP = 38
```

#### Random Forest

```text
TN = 96
FP = 14
FN = 18
TP = 50
```

### ROC-AUC

```text
Logistic Regression = 0.8610
Decision Tree       = 0.8374
Random Forest       = 0.8179
```

ROC curves were generated for all three classifiers.

---

## 12. Task 11 — Handling Class Imbalance

The classification target had the following distribution:

| Class | Count | Percentage |
|---|---:|---:|
| Not Survived | 549 | 61.75% |
| Survived | 340 | 38.25% |

Logistic Regression was tested using three approaches:

1. Baseline Logistic Regression
2. Logistic Regression with `class_weight="balanced"`
3. Logistic Regression with SMOTE applied only to the training data

### Comparison

| Method | Precision | Recall | F1-score |
|---|---:|---:|---:|
| Baseline | 0.7833 | 0.6912 | 0.7344 |
| Class Weight Balanced | 0.7183 | 0.7500 | 0.7338 |
| SMOTE | 0.7353 | 0.7353 | 0.7353 |

### Conclusion

The baseline Logistic Regression achieved the highest precision of 0.7833.

The class-weighted model achieved the highest recall of 0.7500.

SMOTE achieved a balanced precision, recall, and F1-score of 0.7353.

SMOTE was applied only to the training data so that the test set remained completely unseen during resampling.

---

## 13. Task 12 — Random Forest Hyperparameter Tuning

`GridSearchCV` was used to tune the Random Forest classifier.

The following hyperparameters were tested:

```text
n_estimators = [100, 200]
max_depth = [None, 5, 10]
max_features = ["sqrt", "log2"]
```

Five-fold cross-validation was used with F1-score as the scoring metric.

### Best Parameters

```text
n_estimators = 200
max_depth = 5
max_features = sqrt
```

### Best Cross-Validation F1

```text
0.7408
```

The tuned Random Forest was configured with:

```python
oob_score=True
```

### Tuned Random Forest OOB Score

```text
0.8214
```

### Tuned Random Forest Test Results

| Metric | Value |
|---|---:|
| Accuracy | 0.8315 |
| Precision | 0.8654 |
| Recall | 0.6618 |
| F1 | 0.7500 |
| ROC-AUC | 0.8389 |

---

## 14. Task 13 — Fare Prediction Regression

A multivariate Linear Regression model was created to predict `fare`.

The following features were used:

- `pclass`
- `age`
- `sibsp`
- `parch`
- `sex`
- `embarked`

### Regression Results

| Metric | Value |
|---|---:|
| MAE | 21.1386 |
| RMSE | 41.7465 |
| R² | 0.3468 |
| Adjusted R² | 0.3118 |

### Residual Analysis

A residual plot was created to examine the relationship between predicted fare values and residuals.

The residual plot showed increasing variation in residuals as the predicted fare increased.

Several larger residuals were also observed at higher predicted fare values.

This pattern suggests the presence of heteroscedasticity, meaning that the residual variance is not constant across the range of predicted fare values.

---

## 15. Task 14 — Final Model Comparison

Classification and regression results were presented separately because they represent different prediction tasks.

### Classification Models

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.8090 | 0.7833 | 0.6912 | 0.7344 | 0.8610 |
| Decision Tree | 0.7640 | 0.7600 | 0.5588 | 0.6441 | 0.8374 |
| Random Forest | 0.8202 | 0.7812 | 0.7353 | 0.7576 | 0.8179 |
| Tuned Random Forest | 0.8315 | 0.8654 | 0.6618 | 0.7500 | 0.8389 |

### Regression Model

| Model | MAE | RMSE | R² | Adjusted R² |
|---|---:|---:|---:|---:|
| Linear Regression | 21.1386 | 41.7465 | 0.3468 | 0.3118 |

### Final Classifier Recommendation

The tuned Random Forest achieved the highest accuracy of 0.8315 and precision of 0.8654 among the evaluated classifiers.

The original Random Forest achieved higher recall of 0.7353 and a higher F1 score of 0.7576, while Logistic Regression achieved the highest ROC-AUC of 0.8610.

The tuned Random Forest was selected as the final classifier for this experiment based on its overall evaluation results.

---

## 16. Task 15 — Saving and Reloading the Final Pipeline

The complete preprocessing and final Random Forest model were combined into one pipeline.

The fitted pipeline was saved using:

```python
joblib.dump(final_pipeline, "model_pipeline.joblib")
```

The saved pipeline was then reloaded using:

```python
loaded_pipeline = joblib.load("model_pipeline.joblib")
```

A new passenger record was provided to the reloaded pipeline for prediction.

### Example Raw Input

```text
pclass = 1
sex = female
age = 30
sibsp = 0
parch = 0
fare = 80.0
embarked = S
```

### Prediction

```text
Prediction: 1
Survival probability: 0.9676
Result: Survived
```

This confirms that the complete fitted pipeline can be saved, reloaded, and used for prediction on new raw input data.

---

## 17. Module 2 File Structure

```text
analytics/
├── 01_eda.ipynb
├── 02_modeling.ipynb
├── README.md
├── titanic.csv
└── model_pipeline.joblib
```

The offline Titanic dataset is:

```text
analytics/titanic.csv
```

The saved complete machine learning pipeline is:

```text
analytics/model_pipeline.joblib
```

---

## 18. Module 2 End-to-End Workflow

```text
Titanic Dataset
      ↓
Load Dataset Once
      ↓
Save titanic.csv
      ↓
Data Profiling
      ↓
Missing-Value Analysis
      ↓
Data Cleaning
      ↓
EDA and Visualization
      ↓
Exploratory Standardization
      ↓
Stratified Train/Test Split
      ↓
Training-Only Preprocessing
      ↓
Logistic Regression
Decision Tree
Random Forest
      ↓
Model Evaluation
      ↓
Class Imbalance Comparison
      ↓
Random Forest GridSearchCV
      ↓
Tuned Random Forest
      ↓
Fare Regression
      ↓
Final Model Comparison
      ↓
Save Complete Pipeline
      ↓
Reload Pipeline
      ↓
Predict New Raw Input
```

This completes the required Module 2 analytics and predictive modeling workflow.