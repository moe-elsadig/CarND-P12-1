import os.path
import tensorflow as tf
import warnings
from distutils.version import LooseVersion

import helper
import project_tests as tests

# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    # helper.maybe_download_pretrained_vgg(vgg_path)

    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'
    
    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)

    graph = tf.get_default_graph()

    input_w1 = graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob  = graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    vgg_layer3_out  = graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    vgg_layer4_out  = graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    vgg_layer7_out  = graph.get_tensor_by_name(vgg_layer7_out_tensor_name)

    return input_w1, keep_prob, vgg_layer3_out, vgg_layer4_out, vgg_layer7_out


tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes, reg_param=1e-3):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function

    #first layer
    conv_1 = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, padding= 'SAME',
                              kernel_regularizer=tf.contrib.layers.l2_regularizer(reg_param),
                              kernel_initializer=tf.contrib.layers.xavier_initializer(
                                  uniform=True,
                                  seed=None,
                                  dtype=tf.float32
                              ))
    
    #transpose layer
    trans_1 = tf.layers.conv2d_transpose(conv_1, num_classes, 4, 2, padding= 'SAME',
                              kernel_regularizer=tf.contrib.layers.l2_regularizer(reg_param),
                                         kernel_initializer=tf.contrib.layers.xavier_initializer(
                                             uniform=True,
                                             seed=None,
                                             dtype=tf.float32
                                         ))

    #conv for skip layer
    conv_2 = tf.layers.conv2d(vgg_layer4_out, num_classes, 1, padding= 'SAME',
                              kernel_regularizer=tf.contrib.layers.l2_regularizer(reg_param),
                              kernel_initializer=tf.contrib.layers.xavier_initializer(
                                  uniform=True,
                                  seed=None,
                                  dtype=tf.float32
                              ))

    #skip layer
    skip_1 = tf.add(trans_1, conv_2)

    #transpose layer
    trans_2 = tf.layers.conv2d_transpose(skip_1, num_classes, 4, 2, padding= 'SAME',
                              kernel_regularizer=tf.contrib.layers.l2_regularizer(reg_param),
                                         kernel_initializer=tf.contrib.layers.xavier_initializer(
                                             uniform=True,
                                             seed=None,
                                             dtype=tf.float32
                                         ))

    #conv for skip layer
    conv_3 = tf.layers.conv2d(vgg_layer3_out, num_classes, 1, padding= 'SAME',
                              kernel_regularizer=tf.contrib.layers.l2_regularizer(reg_param),
                              kernel_initializer=tf.contrib.layers.xavier_initializer(
                                  uniform=True,
                                  seed=None,
                                  dtype=tf.float32
                              ))

    #skip layer
    skip_2 = tf.add(trans_2, conv_3)

    #transpose layer
    trans_3 = tf.layers.conv2d_transpose(skip_2, num_classes, 16, 8, padding= 'SAME',
                              kernel_regularizer=tf.contrib.layers.l2_regularizer(reg_param),
                                         kernel_initializer=tf.contrib.layers.xavier_initializer(
                                             uniform=True,
                                             seed=None,
                                             dtype=tf.float32
                                         ))
    
    return trans_3

tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function

    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    labels = tf.reshape(correct_label, (-1, num_classes))

    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits= logits, labels= labels))

    train_op = tf.train.GradientDescentOptimizer(learning_rate).minimize(cross_entropy_loss)
    
    return logits, train_op, cross_entropy_loss

tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate, k_prob, l_rate, reg_param):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function

    sess.run(tf.global_variables_initializer())

    for epoch in range(epochs):

        print("\nEpoch:\t", epoch+1, " / ", epochs, "\tk_prob:\t", k_prob, "\tl_rate:\t", l_rate,
              "\treg_param\t", reg_param,"\n\n")

        for image, label in get_batches_fn(batch_size):

            feed_dictionary = {input_image: image,
                                correct_label: label,
                                keep_prob: k_prob,
                                learning_rate: l_rate}
            loss, _ = sess.run([cross_entropy_loss, train_op], feed_dictionary)
            print("Loss:", loss)


    pass
tests.test_train_nn(train_nn)


def run(k_prob=0.5, l_rate=0.001, reg_param=1e-3, curr_tag="none"):

    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)

    learning_rate = tf.placeholder(tf.float32, None)
    correct_label = tf.placeholder(tf.float32, [None, None, None, num_classes])

    batch_size = 2
    epochs = 3

    # Download pretrained vgg model
    # helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function

        input_image, keep_prob, vgg_layer3_out, vgg_layer4_out, vgg_layer7_out = load_vgg(sess, vgg_path)

        print("\n\nVGG loaded!\n\n")

        nn_last_layer = layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes, reg_param)

        print("\n\nLayers set!\n\n")

        logits, train_op, cross_entropy_loss = optimize(nn_last_layer, correct_label, learning_rate, num_classes)

        print("\n\nOptimised!\n\n")

        # TODO: Train NN using the train_nn function

        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
                 correct_label, keep_prob, learning_rate, k_prob, l_rate, reg_param)

        print("\n\nTrained!\n\n")


        # TODO: Save inference data using helper.save_inference_samples
        #  helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob,
                                      input_image, curr_tag)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':

    for i in range(1, 5):
        for j in range(1, 3):
            for k in range(1, 3):

                curr_tag = "klr_" + str(i) + str(j) + str(k) + "_"
                run((0.3*i - 0.1), (0.001**j), (0.001**k), curr_tag)

