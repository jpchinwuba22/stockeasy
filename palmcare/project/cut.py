import sys
from PIL import Image
from rembg import new_session, remove
sess = new_session(sys.argv[1])
for src, dst in zip(sys.argv[2::2], sys.argv[3::2]):
    im = Image.open(src).convert("RGB")
    out = remove(im, session=sess, post_process_mask=True)
    out.save(dst)
    print(dst, out.size, out.split()[-1].getbbox())
