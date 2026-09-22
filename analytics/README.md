# Module 2 — Titanic Analytics and Predictive Modeling

## 1. Module Overview

This module implements a complete analytics and machine learning workflow using the Titanic dataset.

The workflow includes:

- Data loading and profiling
- Missing-value analysis and handling
- Univariate, bivariate, and multivariate analysis
- Exploratory standardization
- Stratified train/test splitting
- Preprocessing using `ColumnTransformer` and `Pipeline`
- Classification using Logistic Regression, Decision Tree, and Random Forest
- Class imbalance comparison
- Random Forest hyperparameter tuning
- Fare regression
- Model comparison
- Saving and reloading the complete machine learning pipeline

The raw Titanic dataset was loaded once using Seaborn and saved as `titanic.csv`. The modeling notebook uses the saved CSV rather than loading the raw dataset again.

---

## 2. Dataset and Data Loading

The Titanic dataset was loaded once using:

```python
df = sns.load_dataset("titanic")

The original dataset contains:

- Rows: 891
- Columns: 15

Immediately after loading, the dataset was saved as:

```python
df.to_csv("titanic.csv", index=False)


### Now paste this immediately below it:

```markdown
The modeling stage reads the saved CSV and does not call `sns.load_dataset("titanic")` again.

---

# Part A — Profiling, Cleaning, and Data Analysis

## 3. Task 1 — Data Profiling

The dataset was inspected using:

```python
df.info()
df.describe()
df.shape

Initial dataset shape:

```text
(891, 15)

### Missing Values

| Column | Missing Values | Missing Percentage |
|---|---:|---:|
| age | 177 | 19.87% |
| embarked | 2 | 0.22% |
| deck | 688 | 77.22% |
| embark_town | 2 | 0.22% |

---

## 4. Task 2 — Missing-Value Handling

The missing-value strategy followed the required percentage-based threshold.

### Age

`age` had **19.87%** missing values.

Since this is between 5% and 30%, median imputation was used.

### Embarked

`embarked` had **0.22%** missing values.

Since the missing percentage was below 5%, the affected rows were removed.

### Embark Town

`embark_town` had **0.22%** missing values.

Since the missing percentage was below 5%, the affected rows were removed.

### Deck

`deck` had **77.22%** missing values.

Because the missing percentage was very high, imputing the column would not be reliable. Therefore, the `deck` column was dropped.

After cleaning, the dataset contained:

```text
889 rows
14 columns

No missing values remained in the cleaned dataset.

---

## 5. Task 3 — Univariate Analysis

Histograms and boxplots were created for both `age` and `fare`.

### Age Outliers

Using the IQR method:

```text
IQR = 17.875
Lower bound = -6.6875
Upper bound = 64.8125
Number of outliers = 11

### Fare Outliers

Using the IQR method:

```text
IQR = 23.0896
Lower bound = -26.724
Upper bound = 65.6344
Number of outliers = 116
### Fare Mean, Median, and Mode

```text
Mean   = 32.2042
Median = 14.4542
Mode   = 8.05

The ordering is:

```text
Mean > Median > Mode
This indicates that the `fare` distribution is positively skewed or right-skewed. The high-fare observations pull the mean upward.

---

## 6. Task 4 — Survival Analysis and Correlation

Survival rates were calculated using boolean masking for:

- Survival rate by sex
- Survival rate by passenger class
- Survival rate by sex and passenger class

### Survival Rate by Sex

| Sex | Survival Rate |
|---|---:|
| Male | 18.89% |
| Female | 74.20% |

Female passengers had a higher survival rate than male passengers in this dataset.

### Survival Rate by Passenger Class

| Passenger Class | Survival Rate |
|---|---:|
| 1 | 62.96% |
| 2 | 47.28% |
| 3 | 24.24% |

The survival rate was highest for first-class passengers and lowest for third-class passengers.

### Survival Rate by Sex and Passenger Class

| Sex | Class | Survival Rate |
|---|---:|---:|
| Male | 1 | 36.89% |
| Male | 2 | 15.74% |
| Male | 3 | 13.54% |
| Female | 1 | 96.81% |
| Female | 2 | 92.11% |
| Female | 3 | 50.00% |

### Correlation Analysis

The correlation matrix was calculated using only:

`survived`, `pclass`, `age`, `sibsp`, `parch`, and `fare`.

The two strongest absolute off-diagonal correlations were:

| Variables | Correlation |
|---|---:|
| pclass and fare | -0.5495 |
| age and pclass | -0.3692 |

The negative correlation between `pclass` and `fare` indicates that lower class numbers, which represent higher passenger classes, were generally associated with higher fares.

The negative correlation between `age` and `pclass` indicates that age tended to be higher among passengers in lower-numbered passenger classes in this dataset.

---

## 7. Task 5 — Multivariate Analysis

Multiple multivariate visualizations were created to understand relationships between different features and survival.

### Chart 1 — Survival by Passenger Class and Sex

The chart compares survival rates across passenger classes for male and female passengers. Female passengers generally had higher survival rates than male passengers across all classes. Survival was also generally higher in first class and lower in third class.

### Chart 2 — Age Distribution by Survival

The age distribution was compared between passengers who survived and those who did not. Most passengers were between approximately 20 and 40 years old. The distributions also show that both younger and older passengers were present among survivors and non-survivors.

### Chart 3 — Fare by Passenger Class

Fare distributions were compared across passenger classes. First-class passengers generally paid higher fares than passengers in second and third class. Several high-fare outliers were also observed, particularly in first class.

### Chart 4 — Age vs Fare by Survival and Passenger Class

The relationship between age and fare was visualized using survival status and passenger class. Most passengers had relatively low fares, while a smaller number of passengers had very high fares. Survival patterns varied across different ages, fares, and passenger classes.

### Chart 5 — Age by Passenger Class and Survival

Age distributions were compared across passenger classes and survival status. The age distribution varied between passenger classes, with first-class passengers generally having a higher median age. Differences between survivors and non-survivors were also visible within the classes.

---

## 8. Task 6 — Exploratory Standardization

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

## 9. Task 7 — Stratified Train/Test Split

The cleaned dataset was divided into training and testing sets using an 80/20 split.

A stratified split was used to maintain a similar proportion of survived and non-survived passengers in both sets.

```text
Training set: 711 rows
Testing set: 178 rows

---

## 10. Task 8 — Data Preprocessing

Preprocessing was performed using a `ColumnTransformer` and `Pipeline`.

The classification models used the following features:

### Numerical Features

- `age`
- `sibsp`
- `parch`
- `fare`

For numerical features:

- Missing values were handled using median imputation.
- Features were standardized using `StandardScaler`.

### Categorical Features

- `sex`
- `embarked`

For categorical features:

- Missing values were handled using the most frequent value.
- Categorical values were converted into numerical form using `OneHotEncoder`.
- `handle_unknown="ignore"` was used to handle unseen categories.

The preprocessing steps were fitted only on the training data and then applied to the test data. This prevents information from the test set from being used during training.

---

## 11. Task 9 — Classification Models

Three classification models were trained using the same training and testing split and the same preprocessing pipeline:

1. Logistic Regression
2. Decision Tree
3. Random Forest

The preprocessing and classifier were combined into complete pipelines so that the same transformations were applied consistently.

### Decision Tree Visualization

The trained Decision Tree was visualized using `plot_tree()` with feature names and class labels:

- `Not Survived`
- `Survived`

The visualization was limited to the first three levels of the tree for better readability.

---

## 12. Task 10 — Model Evaluation and Comparison

The three classification models were evaluated using:

- Confusion Matrix
- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC

### Classification Model Comparison

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.7809 | 0.7544 | 0.6324 | 0.6880 | 0.8265 |
| Decision Tree | 0.7697 | 0.7143 | 0.6618 | 0.6870 | 0.7412 |
| Random Forest | 0.7978 | 0.7759 | 0.6618 | 0.7143 | 0.8211 |

The confusion matrices were also visualized for all three models to compare their classification results.

---

## 13. Task 11 — Handling Class Imbalance

The classification target had an imbalanced distribution, with approximately 61.8% non-survived and 38.2% survived passengers.

Logistic Regression was tested using three approaches:

1. Baseline Logistic Regression
2. Logistic Regression with `class_weight="balanced"`
3. Logistic Regression with SMOTE applied only to the training data

### Comparison

| Method | Precision | Recall | F1-score |
|---|---:|---:|---:|
| Baseline | 0.7544 | 0.6324 | 0.6880 |
| Class Weight Balanced | 0.7500 | 0.7059 | 0.7273 |
| SMOTE | 0.7460 | 0.6912 | 0.7176 |

The baseline model had a recall of 0.6324 and an F1-score of 0.6880.

Using `class_weight="balanced"` increased recall to 0.7059 and F1-score to 0.7273.

SMOTE also improved recall and F1-score compared with the baseline, but the improvement was smaller than with class weighting.

Among the three tested methods, class weighting produced the highest recall and F1-score.

---

## 14. Task 12 — Random Forest Hyperparameter Tuning

GridSearchCV was used to tune the Random Forest classifier.

The following hyperparameters were tested:

- `n_estimators`: 100, 200
- `max_depth`: None, 5, 10
- `max_features`: sqrt, log2

Five-fold cross-validation was used with F1-score as the scoring metric.

### Best Parameters

```text
n_estimators = 100
max_depth = 5
max_features = sqrt

---

## 15. Task 13 — Fare Prediction Regression

A regression model was created to predict `fare` using the following features:

- `pclass`
- `sex`
- `age`
- `sibsp`
- `parch`
- `embarked`

A Linear Regression model was used with preprocessing for numerical and categorical features.

### Regression Results

| Metric | Value |
|---|---:|
| MAE | 21.1386 |
| RMSE | 41.7465 |
| R² | 0.3468 |
| Adjusted R² | 0.3239 |

### Residual Analysis

A residual plot was created to examine the relationship between predicted fare values and residuals.

The residual plot showed increasing variation in residuals as the predicted fare increased. Several large residuals were also observed at higher predicted fare values.

This pattern suggests the presence of heteroscedasticity, meaning that the residual variance is not constant.

---

## 16. Task 14 — Final Model Comparison

### Classification Models

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.7809 | 0.7544 | 0.6324 | 0.6880 | 0.8265 |
| Decision Tree | 0.7697 | 0.7143 | 0.6618 | 0.6870 | 0.7412 |
| Random Forest | 0.7978 | 0.7759 | 0.6618 | 0.7143 | 0.8211 |

### Regression Model

| Model | MAE | RMSE | R² | Adjusted R² |
|---|---:|---:|---:|---:|
| Linear Regression | 21.1386 | 41.7465 | 0.3468 | 0.3239 |

### Final Recommendation

Among the three classification models, Random Forest achieved the highest accuracy (0.7978), precision (0.7759), and F1-score (0.7143). Logistic Regression achieved the highest ROC-AUC score (0.8265). Decision Tree and Random Forest had the same recall of 0.6618. Based on the overall accuracy, precision, and F1-score, Random Forest provides a strong overall classification result for this experiment. The regression model achieved an R² of 0.3468, indicating that the selected features explain a limited portion of the variation in fare.

---

## 17. Task 15 — Saving and Reloading the Final Pipeline

The complete preprocessing and Random Forest model were combined into a single pipeline.

The fitted pipeline was saved using `joblib`:

```python
joblib.dump(final_pipeline, "model_pipeline.joblib")

The saved pipeline was then reloaded using:

```python
loaded_pipeline = joblib.load("model_pipeline.joblib")

A new passenger record was provided to the reloaded pipeline for prediction.

### Example Prediction

```text
Passenger:
pclass = 1
sex = female
age = 25
sibsp = 0
parch = 0
fare = 80.0
embarked = S

The model predicted:

```text
Prediction: Survived

Prediction probabilities:

```text
Not Survived: 0.1189
Survived: 0.8811

This confirms that the complete fitted pipeline can be saved, reloaded, and used for prediction on new input data.