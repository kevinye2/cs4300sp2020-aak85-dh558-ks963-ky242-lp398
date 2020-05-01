import random
import time
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import statistics

class LogReg():
    def __init__(self, tfidf_data):
        self.tfidf_obj = tfidf_data
        self.clean_data = tfidf_data.clean_data
        self.doc_idx_dict = tfidf_data.doc_idx_dict
        self.tfidf = tfidf_data.tfidf
        self.feat = tfidf_data.feat
        self.idf = tfidf_data.idf
        self.term_idx_dict = tfidf_data.term_idx_dict
        self.log_reg_model = None
        self.accum_training = None
        self.accum_label = None

    def resetAll(self):
        self.accum_training = None
        self.accum_label = None
        self.log_reg_model = None

    def addMultipleTraining(self, relevance_data):
        if len(relevance_data) < 1:
            return
        for cur_query in relevance_data:
            cur_query_vector = self.tfidf_obj.vectorizeQuery(cur_query)
            query_dict = relevance_data[cur_query]
            for doc_id in query_dict:
                label = 1 if query_dict[doc_id]['is_relevant'] else -1
                self.addTraining(cur_query_vector, doc_id, label)
        self.retrain()

    def addTraining(self, q, doc_id, label):
        doc_idx = self.doc_idx_dict[doc_id]
        data = self.tfidf[doc_idx:doc_idx + 1]
        concat = sparse.hstack((q, data), format='csr')
        label = label * np.ones((1))
        if self.accum_label is None or self.accum_training is None:
            self.accum_training = concat
            self.accum_label = np.ones((1))
            self.accum_label[0] = label
        else:
            self.accum_training = sparse.vstack((self.accum_training, concat), format='csr')
            self.accum_label = np.append(self.accum_label, label)

    def predictRelevance(self, query, doc_ids):
        if len(doc_ids) < 2 or self.log_reg_model is None:
            return [1] * len(doc_ids)
        q = self.tfidf_obj.vectorizeQuery(query)
        init_pos = self.doc_idx_dict[doc_ids[0]]
        init_csr = sparse.hstack((q, self.tfidf[init_pos]), format='csr')
        for i in range(1, len(doc_ids)):
            cur_pos = self.doc_idx_dict[doc_ids[i]]
            adder = sparse.hstack((q, self.tfidf[cur_pos]), format='csr')
            init_csr = sparse.vstack((init_csr, adder), format='csr')
        prob_predictions = self.log_reg_model.predict_proba(init_csr)
        positive_class_idx = self.log_reg_model.classes_.tolist().index(1)
        prob_labels = [elem[positive_class_idx] for elem in prob_predictions]
        # Any positive probability relevance >= the probability relevance
        # value of the document ranked highest by tfidf cosine similarity
        # or >= the avg probability relevance will be returned as relevant
        baseline_val = prob_labels[0]
        avg = statistics.mean(prob_labels)
        for i, prob in enumerate(prob_labels):
            prob_labels[i] = 1 if prob >= baseline_val or prob >= avg else -1
        return prob_labels

    def retrain(self):
        init_time = time.time()
        try:
            self.log_reg_model = LogisticRegression(random_state=1) \
                .fit(self.accum_training, self.accum_label)
        except Exception:
            self.log_reg_model = None
            print('ERROR ', time.time() - init_time, flush=True)
        print(time.time() - init_time, flush=True)
