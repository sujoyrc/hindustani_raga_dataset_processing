import essentia.standard
from sys import argv
'''
This code uses the essentia library for finding out the tonic. 
'''

src=argv[1]
loader = essentia.standard.MonoLoader(filename=src)
audio = loader()
tonic = essentia.standard.TonicIndianArtMusic(maxTonicFrequency=530)(audio)

print (tonic)