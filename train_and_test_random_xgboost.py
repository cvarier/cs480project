import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn import metrics

# --- Assume all the datasets are located in a folder 'dataset/' within the current working directory ---

# Declare all features which won't be used for training.
# num-authors and prev-games should in theory, correlate with experience level of a team, so these
# should be useful features.
irrelevant_features = ['name', 'slug', 'path', 'category', 'description', 'published', 'modified',
                       'version', 'num-authors', 'competition-num']
# Load training set
train_data = pd.read_csv('dataset/train.csv')
train_data.set_index('id', inplace=True)
train_features = train_data.loc[:, train_data.columns != 'label']

# Drop irrelevant features
train_features.drop(labels=irrelevant_features, axis=1, inplace=True)
train_labels = train_data['label']

# Load testing set
test_features = pd.read_csv('dataset/test.csv')
test_features.set_index('id', inplace=True)
test_features.drop(labels=irrelevant_features, axis=1, inplace=True)

# Convert nan values to empty strings
train_features.fillna("", inplace=True)
test_features.fillna("", inplace=True)

# Convert the 'links' and 'link-tags' features to their counts (aggregation). These features are colon separated.
# We care about these features, since they should, in theory, roughly correlate with the authors' engagement
# and hence, rank in the competition.
def aggregate(x):
    return len(x.split(';')) if x else 0
train_features['links'] = train_features['links'].apply(aggregate)
train_features['link-tags'] = train_features['link-tags'].apply(aggregate)
test_features['links'] = test_features['links'].apply(aggregate)
test_features['link-tags'] = test_features['link-tags'].apply(aggregate)

def log_transform(x):
    return np.sign(x)*np.log(np.abs(x)+1)

# Apply a log transform to all the features to correct the skew in the data
for ind, column in enumerate(train_features.columns):
    train_features[column] = train_features[column].apply(log_transform)
    test_features[column] = test_features[column].apply(log_transform)

# Create a Gradient Boost Classifier (the model).
# Chosen params for XGBClassifier were found by searching a sample space of params
# with GridSearchCV.
clf = XGBClassifier(n_estimators=400)

# Train the model using the training set
clf.fit(train_features, train_labels)

# # Predict using the trained model on the testing set
test_labels = clf.predict(test_features)

# Dump predictions to csv submission file
output_df = pd.DataFrame({'id': pd.Series(test_features.index.values.tolist()),
                          'label': pd.Series(test_labels)})

output_df.to_csv('submission.csv', index=False)

# Predict using the trained model on the training set to determine training accuracy
train_labels_predicted = clf.predict(train_features)

# Output training accuracy
print("Training accuracy is: {}%".format(100*metrics.accuracy_score(train_labels, train_labels_predicted)))

# Determine most important features from classifier
most_important_features = list(zip(train_features.columns, clf.feature_importances_))
most_important_features.sort(key=lambda x: x[1])

print(most_important_features)

