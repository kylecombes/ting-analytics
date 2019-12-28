# Ting Mobile bill analyzer

My family shares a pay-as-you-go Ting Mobile cell service account. This means one person ends up footing the bill for
everyone. Unfortunately, there is not an easy way to view per-line usage data once a billing cycle has closed, so
splitting up a bill based on usage isn't easily possible.

To make splitting the bill according to usage possible, I created this project. It required some reverse-engineering
of the ting.com website combined with a PDF parser. It essentially works like so:

1. Given the account username and password (supplied as arguments), establish a session with the ting.com web server.
2. Download the billing history from the internal Ting API endpoint to get a list of bill IDs.
3. For each bill, get the detailed usage of data, minutes, and texts. This data was available as a CSV and looked like so:
   ```csv
    Date,Device,ICCID,Nickname,Location,Kilobytes,Surcharges ($),Type
    "December 18, 2017",##########,'###################,,United States of America,20614,0.0,GSM
    "December 18, 2017",##########,'###################,,United States of America,920,0.0,GSM
    "December 19, 2017",##########,'###################,,United States of America,6263,0.0,GSM
   ```
   Then sum the usage for each phone line.
4. For each bill, download the PDF invoice. Parse that invoice (using [tabula-py](https://github.com/chezou/tabula-py))
for the total data, calling, and texting usage fees.
5. Split the fees according to line usage.
6. Save the output as a `.xlxs` file.

The code really isn't the most beautiful, but it works. It could break if Ting changes their invoice PDF formatting, as
a Tabula template is needed to parse the PDF. Simply creating a new template and adding it to the `tabula-templates`
folder would resolve the problem.

## Running the code

If you too have a Ting Mobile account, you should be able to use this code to split up your usage by line.

### Steps
1. Ensure Java is installed. (Tabula uses Java, so you'll need it.)
2. Install the Python requirements by running `pip install -r requirements.txt`
3. Run `python get_and_process_bills.py <data_dir> <username> <password>`, replacing `<data_dir>` with the path to the
 directory where cached PDFs and CSVs should be saved and replacing `<username>` and `<password>` with your Ting
account username and password, respectively.
4. Open `Ting usage.xlsx` (saved to `<data_dir>`).