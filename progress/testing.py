from progress.bar import (Bar, ChargingBar, FillingSquaresBar,
                          FillingCirclesBar, IncrementalBar, PixelBar,
                          ShadyBar)

bar = ChargingBar("fefe", max=15)

nb = 60
for i in range(nb):
    bar.goto(float(i/nb*bar.max))
    print(f"{bar.get_str()}")
bar.finish()