"""
Question bank for AI & ML (B.Tech Autonomous, AI24053TH).
30 MCQs, 1 mark each: 5 questions per unit, each unit mapped to its Course Outcome.

  "unit"    : 1 to 6  (Unit-01 to Unit-06)
  "q"       : question text
  "options" : four choices
  "answer"  : index of the correct option (0 = first, 1 = second, ...)
  "image"   : (optional) picture shown above the question, relative to this folder
"""

UNITS = {
    1: ("Unit-01", "CO-1", "Python for AI and Machine Learning"),
    2: ("Unit-02", "CO-2", "Data Preprocessing and Exploratory Data Analysis"),
    3: ("Unit-03", "CO-3", "Supervised Learning Algorithms"),
    4: ("Unit-04", "CO-4", "Unsupervised Learning Techniques"),
    5: ("Unit-05", "CO-5", "Neural Networks and Deep Learning"),
    6: ("Unit-06", "CO-6", "Applications of AI and Machine Learning"),
}

QUESTIONS = [
    # ---- Unit-01 | CO-1 | Python for AI and Machine Learning ----
    {"unit": 1, "q": "Which Python data structure is ordered and mutable and allows duplicate elements?",
     "options": ["Tuple", "Set", "List", "Dictionary"], "answer": 2},
    {"unit": 1, "q": "Which Python data structure stores only unique elements with no defined order?",
     "options": ["List", "Tuple", "Set", "Dictionary"], "answer": 2},
    {"unit": 1, "q": "Which file open mode adds new content to the end of an existing file without erasing it?",
     "options": ["'r'", "'w'", "'a'", "'x'"], "answer": 2},
    {"unit": 1, "q": "The histogram shows the distribution of exam scores. Which Matplotlib function was most likely used to draw it?",
     "options": ["plt.plot", "plt.hist", "plt.scatter", "plt.bar"], "answer": 1,
     "image": "images/q_histogram.png"},
    {"unit": 1, "q": "Which Pandas function reads a CSV file into a DataFrame?",
     "options": ["pd.load_csv()", "pd.read_csv()", "pd.open_csv()", "pd.import_csv()"], "answer": 1},

    # ---- Unit-02 | CO-2 | Data Preprocessing and Exploratory Data Analysis ----
    {"unit": 2, "q": "Which technique creates new input features from existing raw data to improve model performance?",
     "options": ["Feature engineering", "Data imputation", "Outlier detection", "Cross-validation"], "answer": 0},
    {"unit": 2, "q": "Which technique removes less useful input features to reduce dimensionality?",
     "options": ["Feature selection", "Feature engineering", "Data augmentation", "Normalization"], "answer": 0},
    {"unit": 2, "q": "Which method fills missing values in a categorical column with the most frequent value?",
     "options": ["Mode imputation", "Min-max scaling", "Label encoding", "Standardization"], "answer": 0},
    {"unit": 2, "q": "The box plot shows the values of one numeric feature. Which value is an outlier?",
     "options": ["12", "21", "44", "15"], "answer": 2,
     "image": "images/q_boxplot.png"},
    {"unit": 2, "q": "Which plot is most useful in EDA for showing the relationship between two numeric variables?",
     "options": ["Pie chart", "Scatter plot", "Histogram", "Bar chart"], "answer": 1},

    # ---- Unit-03 | CO-3 | Supervised Learning Algorithms ----
    {"unit": 3, "q": "Polynomial regression is best described as an extension of which method?",
     "options": ["Logistic regression", "k-Nearest Neighbor", "Decision tree", "Linear regression"], "answer": 3},
    {"unit": 3, "q": "Which measures are commonly used by a decision tree to choose the best split at a node?",
     "options": ["Gini impurity or entropy", "Euclidean distance", "Eigenvalues", "Learning rate"], "answer": 0},
    {"unit": 3, "q": "In a Support Vector Machine, the optimal decision boundary is the one that maximizes:",
     "options": ["The number of support vectors", "The margin between classes", "The training error", "The number of features"],
     "answer": 1},
    {"unit": 3, "q": "How does k-NN assign a class to a new data point?",
     "options": ["Gradient descent on the weights", "Majority vote of its k nearest neighbors",
                 "Maximum variance direction", "Random sampling of features"],
     "answer": 1},
    {"unit": 3, "q": "The confusion matrix shows the results of a classifier on 100 samples. What is the precision of the model?",
     "options": ["0.67", "0.80", "0.70", "0.57"], "answer": 1,
     "image": "images/q_confusion_matrix.png"},

    # ---- Unit-04 | CO-4 | Unsupervised Learning Techniques ----
    {"unit": 4, "q": "In K-Means clustering, how is each cluster centroid updated in each iteration?",
     "options": ["Median of all data points", "Mean of the points assigned to that cluster",
                 "The farthest data point", "A random data point"],
     "answer": 1},
    {"unit": 4, "q": "DBSCAN forms clusters based on which property of the data?",
     "options": ["Distance to a fixed centroid", "Density of neighboring points",
                 "Depth of a tree", "Class labels"],
     "answer": 1},
    {"unit": 4, "q": "The dendrogram shows hierarchical clustering of five points. Which two points are merged first?",
     "options": ["A and B", "C and D", "A and E", "B and C"], "answer": 0,
     "image": "images/q_dendrogram.png"},
    {"unit": 4, "q": "Principal Component Analysis (PCA) finds directions that capture the maximum:",
     "options": ["Variance in the data", "Mean of the data", "Separation between class labels", "Entropy of the data"],
     "answer": 0},
    {"unit": 4, "q": "Which is a typical application of unsupervised learning?",
     "options": ["Customer segmentation", "Spam classification with labeled emails",
                 "Predicting house prices from labeled sales", "Digit recognition with labeled images"],
     "answer": 0},

    # ---- Unit-05 | CO-5 | Neural Networks and Deep Learning ----
    {"unit": 5, "q": "In the biological neuron model, which part carries the signal away from the cell body?",
     "options": ["Dendrite", "Axon", "Nucleus", "Synaptic receptor"], "answer": 1},
    {"unit": 5, "q": "The plot shows two classes of points at the corners of a square. Can a single perceptron classify them correctly?",
     "options": ["Yes, with one straight line", "No, no single straight line can separate them",
                 "Yes, if the weights start at zero", "Yes, if the learning rate is increased"],
     "answer": 1,
     "image": "images/q_xor.png"},
    {"unit": 5, "q": "How many hidden layers does the neural network in the diagram have?",
     "options": ["0", "1", "2", "3"], "answer": 1,
     "image": "images/q_mlp.png"},
    {"unit": 5, "q": "Backpropagation trains a multilayer perceptron by:",
     "options": ["Randomly changing weights until the error drops",
                 "Propagating error gradients backward through layers using the chain rule",
                 "Clustering the hidden neurons", "Removing the hidden layers"],
     "answer": 1},
    {"unit": 5, "q": "What is the main purpose of the convolutional layers in a CNN?",
     "options": ["To learn filters that detect local spatial features such as edges",
                 "To store the final class labels",
                 "To convert images into text", "To remove all color information"],
     "answer": 0},

    # ---- Unit-06 | CO-6 | Applications of AI and Machine Learning ----
    {"unit": 6, "q": "Which NLP task determines whether a piece of text expresses a positive or negative opinion?",
     "options": ["Image segmentation", "Sentiment analysis", "Edge detection", "Pixel clustering"], "answer": 1},
    {"unit": 6, "q": "The image shows boxes drawn around each object, with a label and confidence score. Which computer vision task does this illustrate?",
     "options": ["Object detection", "Image compression", "Noise removal", "Color inversion"], "answer": 0,
     "image": "images/q_object_detection.png"},
    {"unit": 6, "q": "A content-based recommendation system suggests items that:",
     "options": ["Are randomly selected", "Have features similar to items the user already liked",
                 "Were most recently added to the catalog", "Were rated poorly by the user"],
     "answer": 1},
    {"unit": 6, "q": "In reinforcement learning, an agent improves its behavior by:",
     "options": ["Using only labeled training examples", "Clustering the unlabeled data",
                 "Memorizing the entire dataset", "Maximizing rewards received from its actions in an environment"],
     "answer": 3},
    {"unit": 6, "q": "Which is a major ethical concern in AI systems that are trained on historical data?",
     "options": ["Algorithmic bias leading to unfair decisions", "Faster processing speed",
                 "Larger display screens", "Lower cloud storage cost"],
     "answer": 0},
]

# Spread correct answers evenly across A-D (rotating options keeps their text intact).
for _i, _q in enumerate(QUESTIONS):
    _shift = (_i % 4 - _q["answer"]) % 4
    _q["options"] = [_q["options"][(_k - _shift) % 4] for _k in range(4)]
    _q["answer"] = _i % 4

assert len(QUESTIONS) == 30, "The test must contain exactly 30 questions."
for _u in UNITS:
    assert sum(1 for q in QUESTIONS if q["unit"] == _u) == 5, f"Unit {_u} must have 5 questions."
