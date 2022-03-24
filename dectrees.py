import numpy as np
from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from matplotlib import pyplot as plt

datasets = ['training_data/stringfuzz.csv', 'training_data/woorpje.csv']

data = np.genfromtxt(datasets[0], delimiter=',')
X = data[:, :-1]
y = data[:, -1]


data2 = np.genfromtxt(datasets[1], delimiter=',')
X2 = data2[:, :-1]
y2 = data2[:, -1]

X = np.vstack((X, X2))
y = np.hstack((y, y2))


min_n_class = min([sum(y == e) for e in np.unique(y)])
print(min_n_class)
sampled = []
for ids in [np.where(y == e)[0] for e in np.unique(y)]:
    sampled.extend(ids[np.random.choice(len(ids), size=min_n_class, replace=False)])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=69)

print(X_train.shape, y_train.shape)
print(X_test.shape, y_test.shape)


clf = tree.DecisionTreeClassifier(max_depth=3)
clf.fit(X_train, y_train)

ts = clf.predict(X_test)

print(np.sum(ts == y_test)/len(ts))


fig = plt.figure(figsize=(100,100))
tree.plot_tree(clf, class_names=['CVC4', 'Z3Str3', 'Z3Seq'],
               feature_names=['#asserts', '#vars', '%weq', '%lc', '%regex', '%hol', 'maxlen', '|regex|', 'deg', '#patmat'])
fig.savefig(f'{"_".join([d.split("/")[-1].replace(".csv", "") for d in datasets])}_tree.png')
'''
clf2 = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(8,4), random_state=42)
clf2.fit(X_train, y_train)
ts = clf2.predict(X_test)
print(np.sum(ts == y_test)/len(ts))
'''