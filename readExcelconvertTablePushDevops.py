import asyncio

import aiohttp
import pandas as pd 
from tabulate import tabulate


async def Postcomment(itemid,pat,datatable):
    print("inside post comment")
    auth = aiohttp.BasicAuth("", pat)
    print("")
    commentbody={
             "text": datatable
        }
    
    updateurl=f"https://dev.azure.com/blackbaud/Products/_apis/wit/workItems/{itemid}/comments?api-version=7.1-preview.4"
    async with aiohttp.ClientSession() as session:
        async with session.post(updateurl,auth=auth,json=commentbody) as resp:
        #    res= await resp.json()
           print("")
async def postMessage(datatable):
    url=f"https://dev.azure.com/blackbaud/Products/_apis/wit/wiql?api-version=7.1" 
    pat=""
    auth = aiohttp.BasicAuth("", pat)
    wiql_query = {
        
        "query": """
                SELECT
                    [System.Id],
                    [System.WorkItemType],
                    [System.Title],
                    [System.State],
                    [System.AreaPath],
                    [System.IterationPath]
                FROM workitems
                WHERE
                    [Assigned To] IN ("V-Shravan Togarla")
                    And [System.WorkItemType]="User Story"
                    AND [System.State] IN ("New", "Active","Closed")
                ORDER BY [System.ChangedDate] DESC
        """

    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url,auth=auth,json=wiql_query) as resp:
            data=await resp.json()
            # print(data['workItems'])
            workitems=data.get("workItems",[])
            # print(workitems)
            ids=[item['id'] for item in workitems]
            itemstoupdate=[3914420]
            mathcingitemids=[idx for idx in itemstoupdate if idx in ids ]
            for itemid in mathcingitemids:
                await Postcomment(itemid,pat,datatable)
async def main():
# Load Excel file
    df = pd.read_excel(r"C:\Users\shravantogarla\Downloads\Automation\allwindowserverscmdb.xlsx",usecols=['Name','Used for','Operating System','Supported by','Fully qualified domain name','Operational status'])

    # Optional: fill NaN with empty strings
    df = df.fillna('')

    user_input = input("Enter asset names to search (comma-separated): ")
    search_assets = [x.strip() for x in user_input.split(",") if x.strip()]

    # Filter rows where any column contains any of the search assets
    mask = df.apply(lambda row: row.astype(str).str.contains('|'.join(search_assets), case=False).any(), axis=1)
    df_filtered = df[mask]
    print(df_filtered)


    print(tabulate(df_filtered, headers='keys', tablefmt='grid',showindex=False))
    # datatable=tabulate(df_filtered, headers='keys', tablefmt='pipe',showindex=False)
    datatable=df_filtered.to_html(index=False)

    await postMessage(datatable)
# markdown_table = df_filtered.to_markdown(index=False)

# Print Markdown table
# print(markdown_table)
if __name__ == "__main__":
   asyncio.run(main())