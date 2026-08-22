import pandas as pd

# Load training data
df = pd.read_csv("data/train.csv")

print("Original shape:")
print(df.shape)

print("\nMissing values before cleaning:")
print(df.isnull().sum())

# Numerical columns
numerical_columns = df.select_dtypes(include=["int64", "float64"]).columns

# Fill numerical missing values with median
for column in numerical_columns:
    df[column] = df[column].fillna(df[column].median())

# Categorical columns
categorical_columns = df.select_dtypes(include=["object"]).columns

# Fill categorical missing values
for column in categorical_columns:
    df[column] = df[column].fillna("Unknown")

print("\nMissing values after cleaning:")
print(df.isnull().sum())

print("\nCleaned shape:")
print(df.shape)