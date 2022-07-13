Run an experiment with an air cleaner and a particle meter (these instructions are for PMS5003). See the supplemental material at https://www.tandfonline.com/doi/full/10.1080/02786826.2022.2054674?scroll=top&needAccess=true for the experiment design. Roughly it's:
1. Get a room or an air chamber
2. Start recording on the particle sensor
3. Fill it with a salt aerosol (100g salt / 1 L water put into a nebulizer) while running a mixing fan
4. Shut the nebulizer off after >0.3 has reached its max value of 65535
5. Turn on the air cleaner
6. Shut everything off once particle counts get close to 0.

This repo contains `particulate.py` for logging csv data from a PMS5003 sensor attached to a raspberry pi and a jupyter notebook, `analyze_cadr.ipynb`, for doing the curve fit to determine CADR from the data.

Some ways to attach a PMS5003 to a raspberry pi:
* https://dev.to/nuculabs_dev/pms5003-particulate-matter-sensor-test-run-2mdh
* Or get a breakout board from https://shop.pimoroni.com/products/particulate-matter-sensor-breakout?variant=29493578301523
* Or get an enviro+ from https://shop.pimoroni.com/products/enviro?variant=31155658457171
