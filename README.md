# DLISE: Deep Learning Internal Structure Estimation

## Overview

Sea surface features are strongly related to vertical structure in the ocean (Ex. temperature, salinity, potential density, etc). This trial attempts to predict the vertical structure (temperature and salinity) from sea surface height (SSH) and temperature (SST) by Deep Learning. We assume that Argo profiles are obtained in the North Pacific Subtropical Gyre since internal structures in the ocean depend on the region.

Spacial resolution of our dataset is 0.25 degree x 0.25 degree and it is not enough to resolve submeso-scale (~10km) phenomenon. Therefore our proposed method aims to predict the difference in the order of meso-scale (~100km).

Proposed method predicts three-dimensional grid data with only in-situ observation data (Argo profiles) and do not use any numerical simulation model (Ex. [OFES](http://www.jamstec.go.jp/ofes/)).

## Data

We use following datasets:

- Sea Surface Temperature, Hight and Chlorophyll
  - Download from [Copernicus Marine Environment Monitoring Service (CMEMS)](https://marine.copernicus.eu/) 
  - Spatial resolution : 0.25 x 0.25 grid
  - Time resolution : Daily
  - Data aggregation:
    1. Crop sea surface data to a specified square size. (Ex. 4 x 4 degree)
    2. Find the closest Argo profile to the center of the cropped data and use it as the vertical profile corresponding to the cropped data.
- Argo float
  - [North Pacific Argo Float Data Set](https://ocg.aori.u-tokyo.ac.jp/member/eoka/data/NPargodata/) published by [OKA Eitarou](https://ocg.aori.u-tokyo.ac.jp/member/eoka/)
  - We interpolate profile data by Akima spline

## Training setting

Our method is supervized training of:

- Input : Crroped sea surface temperature, height and chlorophyll map data
- Ground truth : Corresponding vertical profile

## Brief results

IN PRODUCTION

## System information

### Prerequisites

- Docker 20.10.7

In addition to above system requeirements, you need to create [Copernicus Marine Environment Monitoring Service (CMEMS)](https://marine.copernicus.eu/) account and get login ID and PASSWORD.

### Installation

This repogitory will run on the Docker container.

#### Build Docker image

```bash
git clone https://github.com/pystokes/DLISE.git
cd DLISE
docker build -t dlise .
```

#### Run Docker container

```bash
# If you need to download data, need to make directory to store downloaded data.
mkdir -p /archive/DLISE
# Run and enter the container.
docker run -it --rm -v /PATH/TO/DLISE/:/DLISE/ -v /archive/DLISE:/archive/DLISE dlise /bin/bash
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

Change configuratoin in [`tools/download_dataset.sh`](https://github.com/pystokes/DLISE/blob/master/tools/download_dataset.sh). See the shellscript file for examples.

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

Run following command. If you need to download CMEMS dataset, enter CMEMS ID and PASSWORD.

```bash
cd DLISE/tools
sudo bash download_dataset.sh

CMEMS ID: YOUR_ID
CMEMS Password: YOUR_PASWORD
```

After running the above command, you can see directory structure in the specified save directory like below.

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

    After running the above command, you can see directory structure in the specified save directory like below.

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

1. Modify `Requirements` and other parameters in [config.py](https://github.com/pystokes/DLISE/blob/master/config.py). Input directory is the directory created in train phase.

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

1. Set path to trained weights at the `trained_weight_path` in the `config.json` created in train phase.

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
