from sklearn import svm
import sklearn.utils
from scipy.sparse import csr_matrix
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import classification_report
import scipy.stats
import numpy as np

def train_svm(X, y, C, matched_pairs):

    train_indices = []
    test_indices = []
    y_l = len(y)
    for pair in matched_pairs:
        train = []
        test = []
        for ind in range(y_l):
            if ind in pair:
                test.append(ind)
            else:
                train.append(ind)
        train_indices.append(train)
        test_indices.append(test)
    lpo = zip(train_indices, test_indices)
    scores = cross_val_score(svm.LinearSVC(C=C), X, y, cv=lpo, scoring = 'accuracy')
    print("%0.3f +/-%0.3f"
           % (np.mean(scores), scipy.stats.sem(scores)))
    return scores

def top_coefficients(classifier, feature_names, top_features=20):
    coef = classifier.coef_.ravel()
    top_positive_coefficients = np.argsort(coef)[-top_features:]
    top_negative_coefficients = np.argsort(coef)[:top_features][::-1]
    top_coefficients = np.hstack([top_negative_coefficients, top_positive_coefficients])
    names = np.array(feature_names)
    return list(names[top_positive_coefficients]), list(names[top_negative_coefficients]), \
        coef[top_positive_coefficients], coef[top_negative_coefficients]
