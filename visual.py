import matplotlib.pyplot as plt
import numpy as np
import os
from PIL import Image

os.makedirs("visual", exist_ok=True)


def show_mnist(n=20):
    from tensorflow import keras
    (x, y), _ = keras.datasets.mnist.load_data()
    idx = np.random.randint(0, len(x), n)
    x, y = x[idx], y[idx]
    n_col = 5
    n_row = len(x) // n_col
    plt.figure(0, (5, n_row))
    for c in range(n_col):
        for r in range(n_row):
            i = r*n_col+c
            plt.subplot(n_row, n_col, i+1)
            plt.imshow(x[i], cmap="gray_r")
            plt.axis("off")
            # plt.xlabel(y[i])
    plt.tight_layout()
    plt.savefig("visual/mnist.png")
    # plt.show()


def save_gan(model, ep, **kwargs):
    name = model.__class__.__name__.lower()
    if name in ["gan", "wgan", "wgangp", "lsgan", "wgandiv"]:
        imgs = model.call(100, training=False).numpy()
        _save_gan(name, ep, imgs, show_label=False)
    elif name == "cgan" or name == "acgan":
        img_label = np.arange(0, 10).astype(np.int32).repeat(10, axis=0)
        imgs = model.predict(img_label)
        _save_gan(name, ep, imgs, show_label=True)
    elif name in ["infogan"]:
        img_label = np.arange(0, model.label_dim).astype(np.int32).repeat(10, axis=0)
        img_style = np.concatenate(
            [np.linspace(-model.style_scale, model.style_scale, 10)] * 10).reshape((100, 1)).repeat(model.style_dim, axis=1).astype(np.float32)
        img_info = img_label, img_style
        imgs = model.predict(img_info)
        _save_gan(name, ep, imgs, show_label=False)
    elif name == "ccgan":
        if "img" not in kwargs:
            raise ValueError
        input_img = kwargs["img"][:100]
        mask_width = np.random.randint(model.mask_range[0], model.mask_range[1], len(input_img))
        mask = np.ones(input_img.shape, np.float32)
        for i, w in enumerate(mask_width):
            mask_xy = np.random.randint(0, model.img_shape[0] - w, 2)
            x0, x1 = mask_xy[0], w + mask_xy[0]
            y0, y1 = mask_xy[1], w + mask_xy[1]
            mask[i, x0:x1, y0:y1] = 0
        masked_img = input_img * mask
        imgs = model.predict(masked_img)
        imgs = _img_recenter(imgs)
        masked_img = _img_recenter(masked_img.numpy())
        _save_img2img_gan(name, ep, masked_img, imgs)
    elif name == "cyclegan":
        if "img6" not in kwargs or "img9" not in kwargs:
            raise ValueError
        img6, img9 = kwargs["img6"][:50], kwargs["img9"][:50]
        img9_, img6_ = model.g.call(img6, training=False), model.f.call(img9, training=False)
        img = np.concatenate((_img_recenter(img6.numpy()), _img_recenter(img9.numpy())), axis=0)
        imgs = np.concatenate((_img_recenter(img9_.numpy()), _img_recenter(img6_.numpy())), axis=0)
        _save_img2img_gan(name, ep, img, imgs)
    else:
        raise ValueError(name)


def _img_recenter(img):
    return (img + 1) * 255 / 2


def _save_img2img_gan(model_name, ep, img1, img2):
    plt.clf()
    nc, nr = 20, 10
    plt.figure(0, (nc * 2, nr * 2))
    i = 0
    for c in range(0, nc, 2):
        for r in range(nr):
            n = r * nc + c
            plt.subplot(nr, nc, n + 1)
            plt.imshow(img1[i], cmap="gray")
            plt.axis("off")
            plt.subplot(nr, nc, n + 2)
            plt.imshow(img2[i], cmap="gray_r")
            plt.axis("off")
            i += 1

    plt.tight_layout()
    dir_ = "visual/{}".format(model_name)
    os.makedirs(dir_, exist_ok=True)
    path = dir_ + "/{}.png".format(ep)
    plt.savefig(path)


def _save_gan(model_name, ep, imgs, show_label=False):
    imgs = (imgs + 1) * 255 / 2
    plt.clf()
    nc, nr = 10, 10
    plt.figure(0, (nc * 2, nr * 2))
    for c in range(nc):
        for r in range(nr):
            i = r * nc + c
            plt.subplot(nr, nc, i + 1)
            plt.imshow(imgs[i], cmap="gray_r")
            plt.axis("off")
            if show_label:
                plt.text(23, 26, int(r), fontsize=23)
    plt.tight_layout()
    dir_ = "visual/{}".format(model_name)
    os.makedirs(dir_, exist_ok=True)
    path = dir_ + "/{}.png".format(ep)
    plt.savefig(path)


def infogan_comp():
    import tensorflow as tf
    from infogan import InfoGAN
    STYLE_DIM = 2
    LABEL_DIM = 10
    RAND_DIM = 88
    IMG_SHAPE = (28, 28, 1)
    FIX_STD = True
    model = InfoGAN(RAND_DIM, STYLE_DIM, LABEL_DIM, IMG_SHAPE, FIX_STD)
    model.load_weights("./models/infogan/model.ckpt").expect_partial()
    img_label = np.arange(0, 10).astype(np.int32).repeat(10, axis=0)
    noise = tf.repeat(tf.random.normal((1, model.rand_dim)), len(img_label), axis=0)

    def plot(noise, img_label, img_style, n):
        img_label = tf.convert_to_tensor(img_label, dtype=tf.int32)
        img_style = tf.convert_to_tensor(img_style, dtype=tf.float32)
        imgs = model.g.call([noise, img_label, img_style], training=False).numpy()
        plt.clf()
        nc, nr = 10, 10
        plt.figure(0, (nc * 2, nr * 2))
        for c in range(nc):
            for r in range(nr):
                i = r * nc + c
                plt.subplot(nc, nr, i + 1)
                plt.imshow(imgs[i], cmap="gray_r")
                plt.axis("off")
                plt.text(23, 26, int(r), fontsize=23)
        plt.tight_layout()
        model_name = model.__class__.__name__.lower()
        dir_ = "visual/{}".format(model_name)
        os.makedirs(dir_, exist_ok=True)
        path = dir_ + "/style{}.png".format(n)
        plt.savefig(path)

    img_style = np.concatenate(
        [np.linspace(-model.style_scale, model.style_scale, 10)] * 10).reshape((100, 1)).astype(np.float32)
    plot(noise, img_label, np.concatenate((img_style, np.zeros_like(img_style)), axis=1), 1)
    plot(noise, img_label, np.concatenate((np.zeros_like(img_style), img_style), axis=1), 2)


def cvt_gif(folders_or_gan):
    if not isinstance(folders_or_gan, list):
        folders_or_gan = [folders_or_gan.__class__.__name__.lower()]
    for folder in folders_or_gan:
        folder = "visual/"+folder
        fs = [folder+"/" + f for f in os.listdir(folder)]
        imgs = []
        for f in sorted(fs, key=os.path.getmtime):
            if not f.endswith(".png"):
                continue
            try:
                int(os.path.basename(f).split(".")[0])
            except ValueError:
                continue
            img = Image.open(f)
            img = img.resize((img.width//10, img.height//10), Image.ANTIALIAS)
            imgs.append(img)
        path = "{}/generating.gif".format(folder)
        if os.path.exists(path):
            os.remove(path)
        img = Image.new(imgs[0].mode, imgs[0].size, color=(255, 255, 255, 255))
        img.save(path, append_images=imgs, optimize=False, save_all=True, duration=400, loop=0)
        print("saved ", path)


if __name__ == "__main__":
    # show_mnist(20)
    # cgan_res()
    # save_infogan(None, 1)
    # infogan_comp()
    cvt_gif(["wgangp", "wgandiv", "wgan", "cgan", "acgan", "gan", "lsgan", "infogan", "ccgan", "cyclegan"])