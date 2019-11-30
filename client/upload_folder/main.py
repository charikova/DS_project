import csv
import cv2
import matplotlib.pyplot as plt
import numpy
import numpy as np
import random
import mxnet as mx
from mxnet.gluon import data as gdata
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score


def read_traffic_signs(rootpath):
    images = []
    labels = []
    images_names = []
    for c in range(0, 43):
        prefix = rootpath + '/' + format(c, '05d') + '/'
        gt_file = open(prefix + 'GT-' + format(c, '05d') + '.csv')
        gt_reader = csv.reader(gt_file, delimiter=';')
        next(gt_reader)
        for row in gt_reader:
            images_names.append(prefix + row[0])
            images.append(plt.imread(prefix + row[0]))
            labels.append(row[7])
        gt_file.close()
    return images, labels, images_names


def transform(images, shape=(30, 30)):
    result = list()
    for img in images:
        height, width = img.shape[0], img.shape[1]
        if height > width:
            top = bottom = 0
            left = numpy.floor((height - width) / 2)
            right = numpy.ceil((height - width) / 2)
        else:
            left = right = 0
            top = numpy.floor((width - height) / 2)
            bottom = numpy.ceil((width - height) / 2)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        img = cv2.copyMakeBorder(img, int(top), int(bottom), int(left), int(right), int(cv2.BORDER_REPLICATE))
        img = cv2.resize(img, shape)
        result.append(img)
    return result


def split_data(imgs, labels):
    data = []
    for i in range(len(imgs)):
        t = [imgs[i], labels[i]]
        data.append(t)
    random.shuffle(data)
    training_data = []
    testing_data = []
    for i in range(int(len(data) * 0.8)):
        training_data.append(data[0])
        data.pop(0)
    for image in data:
        testing_data.append(image)
    return training_data, testing_data


def frequencies(data):
    freqs = [0 for i in range(43)]
    for i in data:
        freqs[int(i[1])] += 1
    max_amount = max(freqs)
    data = np.array(freqs)
    positions = np.arange(43)
    plt.bar(positions, data, 1)
    plt.xticks(positions + 1 / 2, ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                                   '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
                                   '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
                                   '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',
                                   '40', '41', '42'))
    plt.show()
    return freqs, max_amount


def apply(img, aug, num_rows=2, num_cols=4, scale=2):
    img = mx.ndarray.array(img)
    Y = [aug(img) for _ in range(num_rows * num_cols)]
    return Y


def augmentation(data, freqs, amount):
    for i in range(len(freqs)):
        initial_amount = freqs[i]
        imgs_to_add = amount - initial_amount
        for j in range(imgs_to_add):
            random_data = data
            random.shuffle(random_data)
            initial_img = None
            initial_label = None
            b = 0
            for q in range(len(data)):
                if (int(random_data[q][1]) == int(i)) and (b == 0):
                    initial_img = random_data[q][0]
                    initial_label = random_data[q][1]
                    b = 1
            augmentation_type = random.randint(0, 2)
            tmp_img = None
            if augmentation_type == 0:
                tmp_img = apply(initial_img, gdata.vision.transforms.RandomFlipLeftRight())
            if augmentation_type == 1:
                shape_aug = gdata.vision.transforms.RandomResizedCrop((200, 200), scale=(0.1, 1), ratio=(0.5, 2))
                tmp_img = apply(initial_img, shape_aug)
            if augmentation_type == 2:
                tmp_img = apply(initial_img, gdata.vision.transforms.RandomHue(0.5))
        data.append([tmp_img[0].asnumpy(), initial_label])
        freqs[i] += 1

    return data


def image_normalization(data):
    norm_data = []
    for i in data:
        img = i[0]
        pixels = numpy.asarray(img)
        pixels = pixels.astype('float32')
        pixels /= 255.0
        pixels = pixels.ravel()
        norm_data.append([pixels, i[1]])
    return norm_data


def training(imgs, labels):
    model = RandomForestClassifier(n_estimators=100, max_depth=100)
    model.fit(imgs, labels)
    return model


def evaluate(imgs, test_labels, model):
    predicted_label = model.predict(imgs)
    accuracy = accuracy_score(test_labels, predicted_label)
    precision = precision_score(test_labels, predicted_label)
    recall = recall_score(test_labels, predicted_label)
    return accuracy, precision, recall


def experiment_and_analyze(imgs, labels, test_imgs, true_labels, augment=True):
    shapes = [(30, 30), (40, 40), (50, 50), (60, 60), (70, 70)]
    accuracies = list()
    times = list()

    if augment:
        augmentation(imgs, labels)

    for shape in shapes:
        print('Size:', shape)
        model = training(imgs, labels)
        accuracy, precision, recall = evaluate(test_imgs, true_labels, model)
        print('Accuracy: {}'.format(accuracy))
        accuracies.append(accuracy)

    plt.plot(shapes, accuracies)
    plt.ylabel('accuracy')
    plt.xlabel('shape')
    plt.show()
    plt.plot(shapes, times)
    plt.ylabel('time')
    plt.xlabel('shape')
    plt.show()


print('Data reading...')
train_images, train_labels, train_names = read_traffic_signs('./GTSRB 2/Final_Training/Images')
print('Data reading: DONE')
train_images_resized = []
print('Data transformation...')
train_images_resized = transform(train_images, shape=(30, 30))
print('Data transformation: DONE')
print('Data split...')
new_training_data, new_testing_data = split_data(train_images_resized, train_labels)
print('Data split: DONE')
print('Counting frequencies...')
freqs, max_amount = frequencies(new_training_data)
print('Counting frequencies: DONE')
print("Augmentation...")
new_training_data_augmented = augmentation(new_training_data, freqs, max_amount)
new_testing_data_augmented = augmentation(new_training_data, freqs, max_amount)
print("Augmentation: DONE")
print('Image normalization...')
training_normalized_data = image_normalization(new_training_data)
testing_normalized_data = image_normalization(new_testing_data)
print('Image normalization: DONE')
print('Training model...')
model = training(training_normalized_data)
print('Training model: DONE')
print('Testing model...')
accuracy, precision, recall = evaluate(testing_normalized_data, model)
print('Accuracy score:', accuracy)
print('Testing model: DONE')