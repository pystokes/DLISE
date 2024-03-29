# DLISE: Deep Learning Internal Structure Estimation

## Overview

Vertical structure in the ocean are related to sea surface features (Ex. height, temperature, chlorophyll, etc). This trial attempts to estimate the vertical structure (temperature and salinity) from sea surface features by Deep Learning. We adapt our proposed method to the region of the North Pacific Subtropical Gyre since sea surface and internal structures vary by location.

We use Argo profile and sea surface height, temperature and chlorophyll. Spatial resolution of sea surface data is 0.25 degree x 0.25 degree and it is not enough to resolve submeso-scale (~10km) phenomenon. Therefore our proposed method aims to estimate the difference in the order of meso-scale (~100km). Although this dataset can not resolve submeso-scale impact, shallow layers are more sensitive to the influence of submeso-scale dynamics. To take this into account and estimate shallow layer profile more correctly, we use sea surface chlorophyll since it is expected to be relatively influenced by the submeso-scale dynamics.

Our proposed method has two contributions: first, our method estimates internal structure with only sea surface data. Our approach may enable us to obtain more internal structure data with higher frequency and spatial density than can be obtained with the current Argo program. On the other hand, since this method requires a large amount of Argo profiles, our study argues the importance of the Argo program and the need for further development. Second, we show the importance of the application of machine learning on the oceanography. In recent years, although we can get more dataset in the ocean, they are limited in temporal and spatial resolution. To monitor the state of the ocean, satellite observations can provide a wide range of high-frequency data, however they are limited to the sea surface and insufficient to understand the entire ocean. In our study, we will try to link sea surface data by satellite with data of the interior of the ocean. Our method indicates the potential to obtain more frequent and dense data in the interior of the ocean, and we hope to gain a more detailed understanding of the ocean.

## Dataset

We use following datasets:

- Sea Surface Temperature, Height and Chlorophyll
  - Download from [Copernicus Marine Environment Monitoring Service (CMEMS)](https://marine.copernicus.eu/) 
  - Spatial resolution : 0.25 x 0.25 degrees
  - Time resolution : Daily
  - Data aggregation:
    1. Crop sea surface data to a specified square size. (Ex. 4 x 4 degree)
    2. Find the closest Argo profile to the center of the cropped data and use it as the vertical profile corresponding to the cropped data.
- Argo profile
  - [North Pacific Argo Float Data Set](https://ocg.aori.u-tokyo.ac.jp/member/eoka/data/NPargodata/) published by [OKA Eitarou](https://ocg.aori.u-tokyo.ac.jp/member/eoka/)
  - We interpolate profile data by Akima spline
- Other information
  - Location (latitude and longitude)
    - State of the ocean is strongly related to the location. For example, low temperature in high latitudes, high temperature in low latitudes.
  - Temporal (seasonal) information (__NOT EXPLICITLY IMPLEMENTED__)
    - Since the oceans have seasonal variability, it is impossible to determine whether the differences are temporal or spatial without taking into account temporal information.
    - __Since the combination of latitude, longitude and sea surface data is considered to indirectly contain temporal information, we do not explicitly implemented it.__

## Training information

Our method is supervised training of:

- Input : Cropped sea surface temperature, height and chlorophyll map data
- Ground truth : Corresponding vertical profile

Configurations:

- Common information
  - Latitude : 10 - 40
  - Longitude : 140 - 220
  - Period (Train and Validation):
    - Begin : 2018-01-01
    - End   : 2019-12-31
  - Period (Test):
    - Begin : 2020-01-01
    - End   : 2021-01-17
  - Train-Validation split
    - Train : Validation = 0.75 : 0.25
    - Shuffle before splitting
- Sea surface data
  - Height, temperature and chlorophyll
  - Crop resolution : 4 x 4 degrees
- Argo prifile
  - Minimum pressure: 10 dbar
  - Maximum pressure: 1000 dbar
  - Interpolation interval: 10 dbar

## Brief results

### Estimated results (profiles)

In this section, we compare profiles of ground truth and estimated.

- Ground truth : Red line
- Estimated : Blue line

#### Better cases

Following results are better estimations. We show typical patterns: relatively little change in the vertical direction (Left), significant changing in the intermediate layer (Center) and significant overall changing (Right).

![Fig.1](figs/fig1_betters.png)

#### Bad cases

The two graphs on the left can not estimate the changes in the shallow layers. On the other hand, the two graphs on the right can not estimate well to relatively deep layers.

![Fig.2](figs/fig2_bad1.png)

We show slightly different difficulties. Although the above four graphs indicated incorrect estimations, following results show the difficulties of small scale dynamics. The two graphs on the left can not estimate small scale changes in the layer shallower than 400 dbar. Two graphs on the right shows smaller scale changes in the layer above 200 dbar.

As mentioned in the overview section, the spatial resolution of satellite data is 0.25 x 0.25 degrees, and since our target is to correctly estimate meso-scale variability, estimating such small scale variability is considered difficult by current satellite data.

![Fig.3](figs/fig3_bad2.png)

### Estimation examples

#### Sea surface height

SSH on 2020/10/01 the estimation was performed.
Black lines denote the locations of estimated vertical sections.

- Zonal sections:
  1. Latitude: 32, Longitude: 140-150
  2. Latitude: 38, Longitude: 150-160
- Meridional sections:
  1. Longitude: 144, Latitude: 30-40
  2. Longitude: 154, Latitude: 30-40

![Fig.4](figs/fig4_20201001_ssh.jpg)

#### Zonal sections

- [Left] Latitude: 32, Longitude: 140-150
- [Right] Latitude: 38, Longitude: 150-160

![Fig.5](figs/fig5_20201001_zonals.jpg)

#### Meridional sections

- [Left] Longitude: 144, Latitude: 30-40
- [Right] Longitude: 154, Latitude: 30-40

![Fig.6](figs/fig6_20201001_meridionals.jpg)

### Conclusion

Our proposed method with Machine Learning (Deep Learning) indicated the potential to estimate internal structures of the ocean in the meso-scale resolution by using only satellite data. Since this deep learning model is relatively simple (fully convolutional backbone and some full connection layers), the direct implementation of physical phenomena into the model is expected to improve the accuracy of the estimation. We treated physical parameters and chlorophyll in the same way, but biogeochemical parameters such as chlorophyll are relatively strongly influenced by smaller scale phenomena. Therefore, building a model that can handle these parameters well will also allow us to estimate the internal structure more accurately.

## System information

### Prerequisites

- Docker 20.10.7

In addition to above system requirements, you need to create [Copernicus Marine Environment Monitoring Service (CMEMS)](https://marine.copernicus.eu/) account and get login ID and PASSWORD.

### Installation

This repository will run on the Docker container.

#### Build Docker image

```bash
git clone https://github.com/pystokes/DLISE.git
cd DLISE
docker build -t dlise .
```

#### Run Docker container

```bash
# If you need to download data, you need to make a directory to store downloaded data.
mkdir -p /archive/DLISE
# Run and enter the container.
docker run -it --gpus all --rm -v /PATH/TO/DLISE/:/DLISE/ -v /archive/DLISE/:/archive/DLISE/ dlise /bin/bash
```

### Usage

Commands in this section must be run in the docker container.

#### GPU setting

Only the following patterns to load trained weights are supported.

|Support|Train on|Detect on|
|:---:|:---:|:---:|
|:heavy_check_mark:|Single-GPU|Single-GPU|
|:heavy_check_mark:|Multi-GPU|Single-GPU|
|Not supported|Single-GPU|Multi-GPU|
|:heavy_check_mark:|Multi-GPU|Multi-GPU|

#### Download dataset

Change configuration in [`tools/download_dataset.sh`](https://github.com/pystokes/DLISE/blob/master/tools/download_dataset.sh). See the shellscript file for examples.

```bash
# Config: General (Home directory to save downloaded data)
save_dir="/PATH/TO/SAVE/DATA"
# Config: CMEMS (FTP url to get sea surface data)
cmems_ssh_url="FTP HOME URL"
cmems_sst_url="FTP HOME URL"
cmems_bio_url="FTP HOME URL"
# Config: CMEMS (Years to get sea surface data)
#   Ex. Download data from ${cmems_ssh_url}/{$year} recursively
years='
  YYYY
  YYYY
  YYYY
  ...
'
# Config: Argo
argo_urls='
  LZH FILE 1
  LZH FILE 2
  LZH FILE 3
'
```

Run the following command. If you need to download the CMEMS dataset, enter the CMEMS ID and PASSWORD.

```bash
cd DLISE/tools
sudo bash download_dataset.sh

CMEMS ID: YOUR_ID
CMEMS Password: YOUR_PASWORD
```

After running the above command, you can see the directory structure in the specified save directory like below.

```text
{SAVE_HOME}
   ├── Download_finished
   ├── argo
   │   ├── ARGO_FILE.txt
   │   └── ...
   ├── bio
   │   ├── BIO_FILE.nc
   │   └── ...
   ├── ssh
   │   ├── SSH_FILE.nc
   │   └── ...
   └── sst
       ├── SST_FILE.nc
       └── ...
```

#### Preprocess

1. Modify `Requirements` in [config.py](https://github.com/pystokes/DLISE/blob/master/config.py) at first.

    ```python
    # Requirements : preprocess
    _preprocess_ssh_input_dir = '/PATH/TO/SSH/DIRECTORY'
    _preprocess_sst_input_dir = '/PATH/TO/SST/DIRECTORY'
    _preprocess_bio_input_dir = '/PATH/TO/BIO/DIRECTORY'
    _preprocess_argo_input_dir = '/PATH/TO/ARGO/DIRECTORY'
    _preprocess_save_dir = None
    ```

2. Run script in preprocess mode.

    ```bash
    python execute.py preprocess
    ```

    After running the above command, you can see the directory structure in the specified save directory like below.

    ```text
    {SAVE_HOME}
        ├── bio
        │   ├── 0000001.npy
        │   └── ...
        ├── config.json
        ├── db.csv
        ├── pressure
        │   ├── 0000001.npy
        │   └── ...
        ├── salinity
        │   ├── 0000001.npy
        │   └── ...
        ├── ssh
        │   ├── 0000001.npy
        │   └── ...
        ├── sst
        │   ├── 0000001.npy
        │   └── ...
        └── temperature
            ├── 0000001.npy
            └── ...
    ```

#### Train

1. Modify `Requirements` in [config.py](https://github.com/pystokes/DLISE/blob/master/config.py) at first.

    ```python
    # Requirements : model
    _backbone_pretrained = False
    _input_size = 224
    _objective = 'temperature' # 'temperature' or 'salinity'
    # Requirements : train
    _train_input_dir = '/PATH/TO/DATA/DIRECTORY'
    _train_save_dir = None
    ```

2. Set hyperparameters for train in [config.py](https://github.com/pystokes/DLISE/blob/master/config.py).

    ```python
    self.train = {
        'input_dir': _train_input_dir,
        'save_dir': _train_save_dir,
        'split_random_seed': 0,
        'resize_method': 'bicubic',
        'resume_weight_path': '',
        'num_workers': 0,
        'batch_size': 512,
        'epoch': 1000,
        'shuffle': True,
        'weight_save_period': 5,
        'weighted_loss': True,
        'optimizer': {
            'optim_type': 'adam',
            'sgd': {
                'lr': 5e-4,
                'wait_decay_epoch': 100,
                'momentum': 0.9,
                'weight_decay': 5e-4,
                'T_max': 10
            },
            'adam': {
                'lr': 0.001,
                'betas': (0.9, 0.999),
                'eps': 1e-08,
                'weight_decay': 0,
                'amsgrad': False
            }
        }
    }
    ```

3. Run script in train mode.

    ```bash
    python execute.py train [-g GPU_ID]
    ```

    If train on multi-GPU, separate GPU IDs with commas.

    ```bash
    # Example: Use two GPUs (0 and 1)
    python execute.py train -g 0,1
    ```

#### Evaluation

1. Modify `Requirements` and other parameters in [config.py](https://github.com/pystokes/DLISE/blob/master/config.py). Input directory is the directory created in the train phase.

    ```python
    # Requirements : evaluate
    _evaluate_input_dir = '/PATH/TO/DATA/DIRECTORY'
    ```

    ```python
    self.evaluate = {
        'trained_weight_path': '/PATH/TO/PRETRAINED/WEIGHT',
        'objective': _objective,
        'input_dir': _evaluate_input_dir,
        'n_figure': 100 # The number of profile figures
    }
    ```

2. Run script in evaluation mode.

    ```bash
    python execute.py evaluate
    ```

#### Prediction

1. Set path to trained weights at the `trained_weight_path` in the `config.json` created in the train phase.

    ```json
    "predict": {
        ...,
        "trained_weight_path": "/PATH/TO/PRETRAINED/WEIGHT",
        ...,
    }
    ```

2. Change other configurations in `predict`.

    ```json
    "predict": {
        "crop": {
            "zonal": 4,
            "meridional": 4
        },
        "objectives": {
            "20201001": {
                "lat_min": 10,
                "lat_max": 40,
                "lon_min": 140,
                "lon_max": 220
            },
            "20201015": {
                "lat_min": 10,
                "lat_max": 40,
                "lon_min": 140,
                "lon_max": 220
            }
        },
        "trained_weight_path": "/PATH/TO/PRETRAINED/WEIGHT",
        "save_results": true
    }
    ```

3. Run script in detection mode.

    __Note:__ `/INPUT/DIR` is the directory `{SAVE_HOME}` created in the section [Download dataset](#download-dataset)

    ```bash
    python execute.py predict -c /PATH/TO/config.json -x /INPUT/DIR [-y /OUTPUT/DIR]
    ```

#### Visualization

1. Modify [config.py](https://github.com/pystokes/DLISE/blob/master/config.py) at first.


    ```python
    self.visualize = {
        'predicted_dir': '/PATH/TO/PREDICTION/DIR',
        'objectives': [
            {
                'date': '20201001',
                'map': {
                    'draw': True,
                    'lat_min': 10,
                    'lat_max': 40,
                    'lon_min': 140,
                    'lon_max': 220
                },
                'draw_lines_on_map': True,
                'zonal_sections': [
                    {
                        'lat': 20,
                        'lon_min': 170,
                        'lon_max': 180,
                        'pre_min': 10,
                        'pre_max': 1000
                    },
                    {
                        'lat': 30,
                        'lon_min': 180,
                        'lon_max': 190,
                        'pre_min': 10,
                        'pre_max': 1000
                    }
                ],
                'meridional_sections': [
                    {
                        'lon': 150,
                        'lat_min': 20,
                        'lat_max': 30,
                        'pre_min': 10,
                        'pre_max': 1000
                    },
                    {
                        'lon': 160,
                        'lat_min': 30,
                        'lat_max': 40,
                        'pre_min': 10,
                        'pre_max': 1000
                    },
                ]
            },
            {
                'date': '20201015',
                'map': {
                    'draw': True,
                    'lat_min': 10,
                    'lat_max': 40,
                    'lon_min': 140,
                    'lon_max': 220
                },
                'draw_lines_on_map': True,
                'zonal_sections': [
                    {
                        'lat': 20,
                        'lon_min': 170,
                        'lon_max': 180,
                        'pre_min': 10,
                        'pre_max': 1000
                    }
                ],
                'meridional_sections': [
                    {
                        'lon': 150,
                        'lat_min': 20,
                        'lat_max': 30,
                        'pre_min': 10,
                        'pre_max': 1000
                    },
                    {
                        'lon': 160,
                        'lat_min': 30,
                        'lat_max': 40,
                        'pre_min': 10,
                        'pre_max': 1000
                    },
                ]
            }
        ]
    }
    ```

2. Run script in visualization mode.

    ```bash
    python execute.py visualize
    ```
