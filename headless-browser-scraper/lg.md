Step 1:
Fetch https://www.lg.com/ca_en/support/product-support/?csSalesCode=<model name here>

Step 2:
Wait for js bundle to render (5 seconds)

Step 3:
Check for <div class="manualList"> 

Step 4:
Checked for element nested within .manualList: <div class="c-resources__item--download-button">.<a>:
<a href="https://gscs-b2c.lge.com/downloadFile?fileId=AuXvio3SwwFIKahuKkYw" class="
												c-btn-arrow c-btn-download
										" data-link-name="true" data-link-destination="true" data-link-menu="true" data-link-page-type="true" target="_blank" rel="noreferrer" aria-describedby="download-manual-label-manualList-0" data-cmp-data-layer=""><span class="sr-only">English</span></a>

Step 5: Navigate to the [href] and downlod the PDF and validate that it matches what we requested.