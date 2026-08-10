import matplotlib.pyplot as plt

METHODS = [
    "Naive Bayes and SVM",
    "Decision Tree",
    "Ensemble Model",
    "SVM",
    "Evolutionary Genetic Algorithm",
    "Proposed Solution"
]
ACCURACIES = [90, 94.15, 88, 89.66, 95, 96.5]
BAR_COLORS = [
    'royalblue', 'slateblue', 'mediumslateblue', 'blueviolet',
    'darkorchid', 'mediumorchid'
]
OUTPUT_FILE = 'accuracy_comparison.png'

plt.figure(figsize=(10, 6))

bars = plt.bar(methods, accuracies, color=bar_colors, edgecolor='black', linewidth=1)

for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{height}%',
             ha='center', va='bottom')

plt.ylabel('Accuracy (%)')
plt.xlabel('Techniques')
plt.xticks(rotation=45, ha="right")

plt.tight_layout()

plt.savefig('accuracy_comparison.png', dpi=160, bbox_inches='tight')

plt.show()