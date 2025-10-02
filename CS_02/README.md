This is a small and reversible image encrypt/decrypt tool implemented in Pyhton using simple pixel permutation and XOR keystream.

**How it works.**\
Permutation: Pixels are shuffled using a pseudo-random permutation generated from a numeric seed.\
XOR keystream: a determinitic byte keystream (also from the seed) is XORed with RGB channels to add diffusion.\
Reversal: Using the same seed can regenerate the permutation and keystream to undo XOR and unshuffle the pixels\
restoring the original image exactly.

<img width="683" height="54" alt="image" src="https://github.com/user-attachments/assets/5e48990d-e95f-4a7e-96e6-333157cd0c94" />\
'python3 pixle.py encrypt image.png image.enc.png --seed 12345'\
encrypt is the argument we passed in: we want to encrypt the image\
image.png: random image\
image.enc.png: name of encrypted image\
--seed 12345: is the numeric seed for the random number generator (RNG) that gives us the 'shuffle order' and 'extra scrambling of pixels'
After running the program, if I check my folder I have a file named 'image.enc.png' and if we check it we see the following:\
Encrypted:\
<img width="514" height="422" alt="image enc" src="https://github.com/user-attachments/assets/3ca05077-56d0-4261-a592-bc542a54e95b" />\
Original:\
<img width="514" height="422" alt="image" src="https://github.com/user-attachments/assets/04ec9f33-ae45-4add-8a19-b6d12566b031" />\
We can also reverse the encrypted image by running 'python3 pixel.py decrypt image.enc.png image.dec.png --seed 12345'.
