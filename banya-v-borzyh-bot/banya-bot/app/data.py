import gspread

gc = gspread.service_account(filename='./credentials.json')

async def get_data():
    sh = gc.open('Баня FAQ').sheet1
    return sh.get_all_records()

