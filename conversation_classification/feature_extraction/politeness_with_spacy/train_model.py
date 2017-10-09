from __future__ import unicode_literals

import json

import random
import cPickle
import numpy as np
import os

from sklearn import svm
from scipy.sparse import csr_matrix
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import StratifiedKFold

from features.vectorizer import PolitenessFeatureVectorizer
from sklearn.model_selection import LeaveOneOut

"""
Sample script to train a politeness SVM

Buckets documents by politeness score
   'polite' if score > 0.0
   'impolite' otherwise
Could also elect to not bucket
and treat this as a regression problem
"""


def train_svm(documents):
    """
    :param documents- politeness-annotated training data
    :type documents- list of dicts
        each document contains a 'text' field with the text of it.

    :param ntesting- number of docs to reserve for testing
    :type ntesting- int

    returns fitted SVC, which can be serialized using cPickle
    """
    # Generate and persist list of unigrams, bigrams
    documents = PolitenessFeatureVectorizer.preprocess(documents) 
    with open("features.json", "w") as w:
         json.dump(documents, w)
    print "DUMPED"

    PolitenessFeatureVectorizer.generate_bow_features(documents)

    # For good luck
    random.shuffle(documents)
    X, y = documents2feature_vectors(documents)

    print "Fitting"
    clf = svm.SVC(C=0.02, kernel='linear', probability=True)
 #   loocv = LeaveOneOut()
 #   scores = cross_val_score(clf, X, y, cv=loocv)
    clf.fit(X, y)

#    print(scores.mean())
#    print scores

    return clf


def documents2feature_vectors(documents):
    vectorizer = PolitenessFeatureVectorizer()
    fks = False
    X, y = [], []
    for d in documents:
        fs = vectorizer.features(d)
        if not fks:
            fks = sorted(fs.keys())
        fv = [fs[f] for f in fks]
        # If politeness score > 0.0,
        # the doc is polite, class=1
        l = 1 if d['score'] > 0.0 else 0
        X.append(fv)
        y.append(l)
    X = csr_matrix(np.asarray(X))
    y = np.asarray(y)
    return X, y

MODEL_FILENAME = os.path.join(os.path.split(__file__)[0], 'politeness-svm.p')   

if __name__ == "__main__":


    """
    Train a model off the wikipedia dataset
    """

    from train_documents import DOCUMENTS

    clf = train_svm(DOCUMENTS)
    cPickle.dump(clf, open(MODEL_FILENAME, 'w')) 
