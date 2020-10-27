## parcel_info
A simple python delivery tracker for FedEx, UPS and USPS.

It suppose to do one thing:
Return the estimated or actual delivery time, and the current status.

The code itself might contain more output, for future work.

The system uses public API (except UPS). If you have large volume, you should not use this, 
but instead seek to obtain actual API keys from the carriers and work with their system.

The code is just for my own use, hence it will not support more features unless I need those features. 


# Requirement

This code requires a lot of libraries. Need to un the following first.

`pip install yaml requests xmltodict dict2xml tabulate bs4 tracking_url dateparser`

You need a `config.yml` file. You also need to [get an access key for UPS API](https://www.ups.com/upsdeveloperkit?loc=en_US).
See `example_config.yml` to see what you need.

# Usage

`python main.py filename`

The file contains 1 line per tracking. This output each tracking and its associated status and delivery eta.

If filename not specified, it default to reading `TRACKING_FILE` from `config.yml`.

`python status.py tracking_number`

It output the status and eta for a single tracking number.
