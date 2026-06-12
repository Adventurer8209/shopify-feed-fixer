from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import PlainTextResponse, HTMLResponse
from app.models import GoogleShoppingProduct
import httpx
import pandas as pd
import io

app = FastAPI(title="Shopify Feed Fixer API")

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def web_interface():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FeedFixer | Shopify Inventory Sync</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }
            .drag-active { border-color: #2563eb !important; background-color: #eff6ff !important; }
        </style>
    </head>
    <body class="text-slate-900 antialiased selection:bg-blue-100">
        
         <nav class="bg-white/90 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
            <div class="max-w-6xl mx-auto px-6 py-5 flex justify-between items-center">
                <a href="/" class="font-extrabold text-2xl tracking-tight text-slate-900 hover:opacity-80 transition">FeedFixer<span class="text-blue-600">.</span></a>
                <div class="flex items-center gap-3 sm:gap-5">
                    <div class="hidden sm:flex items-center gap-5">
                        <a href="#pricing" class="text-sm font-semibold text-slate-600 hover:text-blue-600 transition">Pricing</a>
                        <a href="#faq" class="text-sm font-semibold text-slate-600 hover:text-blue-600 transition">FAQ</a>
                    </div>
                    <a href="#" class="bg-slate-900 text-white px-4 py-2 sm:px-5 sm:py-2.5 rounded-full text-xs sm:text-sm font-bold hover:bg-slate-800 transition shadow-sm whitespace-nowrap">Install App</a>
                </div>
            </div>
        </nav>

        <div class="max-w-5xl mx-auto px-6 py-16">
            
            <div class="text-center mb-20">
                <h1 class="text-5xl md:text-6xl font-extrabold mb-6 tracking-tight text-slate-900">
                    Perfect Google Feeds.<br/>
                    <span class="text-blue-600">Zero Manual Work.</span>
                </h1>
                <p class="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto font-medium leading-relaxed">
                    Upload your supplier's messy CSV. We automatically format prices, protect SKUs, and generate a live link for Shopify & Google Merchant Center.
                </p>
            </div>

            <div class="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-200 overflow-hidden mb-16">
                <div class="bg-slate-900 px-8 py-6 border-b border-slate-800 flex justify-between items-center">
                    <h2 class="text-xl font-bold text-white">1. Test with your own data</h2>
                    <span class="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">Free Preview</span>
                </div>
                
                <div class="p-8">
                    <div id="dropZone" class="border-2 border-dashed border-slate-300 rounded-2xl p-10 text-center hover:bg-slate-50 transition cursor-pointer relative group">
                        <input type="file" id="fileInput" accept=".csv" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10">
                        <div class="mx-auto w-16 h-16 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                        </div>
                        <h3 class="text-lg font-bold text-slate-900 mb-1">Upload a raw supplier CSV</h3>
                        <p class="text-sm text-slate-500">Drag and drop your file here, or click to browse</p>
                    </div>

                    <div id="previewResult" class="hidden mt-8">
                        <div class="flex items-center gap-2 mb-3">
                            <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                            <h3 class="font-bold text-slate-900">Cleaned Result (First 30 rows):</h3>
                        </div>
                        <div class="bg-slate-900 rounded-xl p-5 border border-slate-800 shadow-inner">
                            <pre id="cleanJson" class="text-emerald-400 font-mono text-sm overflow-x-auto"></pre>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-3xl shadow-xl overflow-hidden text-white relative mb-24">
                <div class="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
                <div class="p-10 relative z-10">
                    <h2 class="text-2xl font-bold mb-3">2. Generate Auto-Updating Feed</h2>
                    <p class="text-blue-100 mb-8 max-w-xl">Paste the live URL of your supplier's feed. We'll give you a new link that outputs a perfectly formatted CSV for your Shopify import app.</p>
                    
                    <div class="flex flex-col md:flex-row gap-4">
                        <input type="text" id="rawUrl" placeholder="https://supplier.com/inventory.csv" 
                               class="flex-1 px-6 py-4 rounded-xl text-slate-900 font-medium focus:ring-4 focus:ring-blue-400 focus:outline-none placeholder-slate-400">
                        
                        <button onclick="generateLink()" class="bg-white text-blue-700 font-extrabold text-lg px-8 py-4 rounded-xl hover:bg-slate-50 hover:scale-105 transition-all shadow-lg whitespace-nowrap">
                            Create Live Link
                        </button>
                    </div>

                    <div id="resultBox" class="hidden mt-6 p-6 bg-blue-800/50 border border-blue-400/30 rounded-xl backdrop-blur-sm">
                        <p class="text-sm text-blue-200 font-bold mb-2">🎉 Your clean, auto-updating URL is ready:</p>
                        <textarea id="cleanLink" readonly class="w-full text-sm p-4 border border-blue-500/50 rounded-lg bg-blue-900/50 text-white h-20 focus:outline-none" onclick="this.select()"></textarea>
                        <p class="text-xs text-blue-300 mt-3 font-medium">Use this URL in your store. It returns a fully validated CSV file.</p>
                    </div>
                </div>
            </div>

            <div id="pricing" class="mb-24 text-center">
                <h2 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">Simple, Transparent Pricing</h2>
                <p class="text-lg text-slate-600 mb-10">One plan. Unlimited feed cleanings. No hidden fees.</p>
                
                <div class="bg-white rounded-3xl shadow-xl border border-slate-200 max-w-md mx-auto p-10 transform hover:-translate-y-1 transition duration-300">
                    <h3 class="text-2xl font-bold text-slate-900">Pro Merchant</h3>
                    <div class="my-6">
                        <span class="text-6xl font-extrabold text-slate-900">$29</span><span class="text-xl text-slate-500 font-medium">/mo</span>
                    </div>
                    <p class="text-emerald-600 font-bold mb-8 bg-emerald-50 inline-block px-4 py-1.5 rounded-full text-sm">14-Day Free Trial</p>
                    
                    <ul class="text-left space-y-4 mb-10">
                        <li class="flex items-center gap-3 text-slate-700 font-medium">
                            <span class="text-blue-500 text-xl">✓</span> Fix infinite CSV feeds automatically
                        </li>
                        <li class="flex items-center gap-3 text-slate-700 font-medium">
                            <span class="text-blue-500 text-xl">✓</span> Rescue broken SKUs & leading zeros
                        </li>
                        <li class="flex items-center gap-3 text-slate-700 font-medium">
                            <span class="text-blue-500 text-xl">✓</span> Smart European/US price formatting
                        </li>
                    </ul>
                    
                    <a href="#" class="block w-full bg-slate-900 text-white font-bold text-lg py-4 rounded-xl hover:bg-slate-800 transition shadow-md">
                        Start 14-Day Free Trial
                    </a>
                    <p class="text-xs text-slate-400 mt-4">Cancel anytime via Shopify billing.</p>
                </div>
            </div>

            <div id="faq" class="mb-24 max-w-3xl mx-auto">
                <h2 class="text-3xl font-extrabold text-slate-900 mb-10 text-center">Frequently Asked Questions</h2>
                <div class="space-y-6">
                    <div class="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm">
                        <h4 class="font-bold text-slate-900 text-lg mb-2">How often does my feed update?</h4>
                        <p class="text-slate-600 leading-relaxed">Your feed updates dynamically. Whenever Shopify or Google requests your custom link, our engine instantly pulls the latest data from your supplier and cleans it on the fly.</p>
                    </div>
                    <div class="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm">
                        <h4 class="font-bold text-slate-900 text-lg mb-2">Are my store and supplier data safe?</h4>
                        <p class="text-slate-600 leading-relaxed">Absolutely. We process data strictly in memory. We do not store your CSV files, supplier links, or inventory data on our hard drives.</p>
                    </div>
                    <div class="bg-white p-7 rounded-2xl border border-slate-200 shadow-sm">
                        <h4 class="font-bold text-slate-900 text-lg mb-2">What formats do you support?</h4>
                        <p class="text-slate-600 leading-relaxed">Currently, we support the most problematic format: CSV (Comma-Separated Values). We automatically handle broken delimiters, floating commas in prices, and missing values.</p>
                    </div>
                </div>
            </div>

        </div>

        <!-- ПОДВАЛ (FOOTER) -->
        <footer class="border-t border-slate-200 bg-white pt-12 pb-16 text-center">
            <div class="flex flex-wrap justify-center items-center gap-6 md:gap-10 mb-6 text-sm font-semibold text-slate-500">
                <a href="/terms" class="hover:text-blue-600 transition">Terms of Service</a>
                <a href="/privacy" class="hover:text-blue-600 transition">Privacy Policy</a>
                <a href="mailto:feedfixer.support@gmail.com" class="hover:text-blue-600 transition">Email Support</a>
            </div>
            <p class="text-slate-400 text-sm">&copy; 2026 FeedFixer. Built with care for E-commerce.</p>
        </footer>

        <script>
            // Логика Drag & Drop
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');

            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-active');
            });
            dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-active'));
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-active');
                if (e.dataTransfer.files.length) {
                    fileInput.files = e.dataTransfer.files;
                    handleFileUpload(fileInput.files[0]);
                }
            });

            fileInput.addEventListener('change', () => {
                if (fileInput.files.length) handleFileUpload(fileInput.files[0]);
            });

            async function handleFileUpload(file) {
                if (!file.name.endsWith('.csv')) {
                    alert("Please upload a CSV file.");
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                document.getElementById('previewResult').classList.remove('hidden');
                document.getElementById('cleanJson').textContent = "Analyzing structure & cleaning data...";
                document.getElementById('cleanJson').className = "text-blue-400 font-mono text-sm overflow-x-auto animate-pulse";

                try {
                    const response = await fetch('/api/v1/preview-file', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();
                    
                    if (response.ok) {
                        document.getElementById('cleanJson').textContent = JSON.stringify(data.cleaned_data, null, 2);
                        document.getElementById('cleanJson').className = "text-emerald-400 font-mono text-sm overflow-x-auto";
                    } else {
                        document.getElementById('cleanJson').textContent = "Error: " + data.detail;
                        document.getElementById('cleanJson').className = "text-red-400 font-mono text-sm overflow-x-auto";
                    }
                } catch (err) {
                    document.getElementById('cleanJson').textContent = "Connection error.";
                }
            }

            // Логика генератора ссылок
            function generateLink() {
                const rawUrl = document.getElementById('rawUrl').value;
                if (!rawUrl) {
                    alert("Please enter a valid supplier URL");
                    return;
                }
                const baseUrl = window.location.origin;
                const cleanUrl = `${baseUrl}/api/v1/fix-feed?url=${encodeURIComponent(rawUrl)}`;
                
                document.getElementById('cleanLink').value = cleanUrl;
                document.getElementById('resultBox').classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/v1/preview-file", tags=["Sandbox"])
async def preview_csv_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')), dtype=str, nrows=30)
        raw_products = df.to_dict(orient="records")
        
        cleaned_feed = []
        for item in raw_products:
            try:
                mapped_data = {
                    "sku": item.get("id") or item.get("sku") or item.get("SKU"),
                    "title": item.get("title") or item.get("name"),
                    "price": item.get("price") or item.get("msrp"),
                    "availability": item.get("availability") or item.get("stock", "in_stock")
                }
                valid_product = GoogleShoppingProduct(**mapped_data)
                cleaned_feed.append(valid_product.model_dump())
            except Exception:
                pass 
                
        return {"cleaned_data": cleaned_feed}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not process file. Ensure it is a valid CSV.")

@app.get("/api/v1/fix-feed")
async def fix_supplier_feed(url: str = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
        df = pd.read_csv(io.StringIO(response.text), dtype=str)
        raw_products = df.to_dict(orient="records")
        
        cleaned_feed = []
        for item in raw_products:
            try:
                mapped_data = {
                    "sku": item.get("id") or item.get("sku") or item.get("SKU"),
                    "title": item.get("title") or item.get("name"),
                    "price": item.get("price") or item.get("msrp"),
                    "availability": item.get("availability") or item.get("stock", "in_stock")
                }
                valid_product = GoogleShoppingProduct(**mapped_data)
                cleaned_feed.append(valid_product.model_dump())
            except Exception:
                pass
        
        if not cleaned_feed:
            raise HTTPException(status_code=400, detail="No valid products found after cleaning")

        out_df = pd.DataFrame(cleaned_feed)
        csv_buffer = io.StringIO()
        out_df.to_csv(csv_buffer, index=False)
        
        return PlainTextResponse(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="clean_feed.csv"'}
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dummy-supplier", tags=["Testing"])
async def dummy_supplier_csv():
    csv_content = """sku,title,price,availability\n00123-A,Premium T-Shirt,"15,50 €",In Stock\n00124-B,Blue Coffee Mug,$ 9.99,sold_out\n,Broken Item Without SKU,0,\n00789-X,Wireless Headphones,"1.250,00 €",available"""
    return PlainTextResponse(content=csv_content, media_type="text/csv")

@app.get("/privacy", response_class=HTMLResponse, tags=["Legal"])
async def privacy_policy():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Privacy Policy | FeedFixer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&display=swap" rel="stylesheet">
        <style>body { font-family: 'Plus Jakarta Sans', sans-serif; }</style>
    </head>
    <body class="bg-slate-50 text-slate-900 py-10 px-6">
        <div class="max-w-3xl mx-auto bg-white p-10 rounded-2xl shadow-sm border border-slate-200">
            <a href="/" class="text-blue-600 font-bold text-sm mb-8 inline-block hover:underline">&larr; Back to Home</a>
            <h1 class="text-3xl font-extrabold mb-6">Privacy Policy</h1>
            <p class="text-sm text-slate-500 mb-8">Last updated: June 2026</p>
            <div class="space-y-6 text-slate-700 leading-relaxed">
                <h2 class="text-xl font-bold text-slate-900">1. Information We Collect</h2>
                <p>When you install the FeedFixer app ("the App"), we automatically access certain types of information from your Shopify account necessary for the App to function properly. This includes basic store information and product inventory data strictly for the purpose of formatting your feeds.</p>
                
                <h2 class="text-xl font-bold text-slate-900">2. How We Use Your Information</h2>
                <p>We use the data collected strictly to provide the FeedFixer service. We process your supplier CSV links dynamically in memory. We do not permanently store your inventory data, product descriptions, or supplier URLs on our databases.</p>
                
                <h2 class="text-xl font-bold text-slate-900">3. Information Sharing</h2>
                <p>We do not sell, rent, or trade your personal or store information to third parties. Data is only shared with Shopify APIs as required to synchronize your inventory.</p>
                
                <h2 class="text-xl font-bold text-slate-900">4. Contact Us</h2>
                <p>If you have questions regarding this Privacy Policy, please contact us at feedfixer.support@gmail.com.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/terms", response_class=HTMLResponse, tags=["Legal"])
async def terms_of_service():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Terms of Service | FeedFixer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&display=swap" rel="stylesheet">
        <style>body { font-family: 'Plus Jakarta Sans', sans-serif; }</style>
    </head>
    <body class="bg-slate-50 text-slate-900 py-10 px-6">
        <div class="max-w-3xl mx-auto bg-white p-10 rounded-2xl shadow-sm border border-slate-200">
            <a href="/" class="text-blue-600 font-bold text-sm mb-8 inline-block hover:underline">&larr; Back to Home</a>
            <h1 class="text-3xl font-extrabold mb-6">Terms of Service</h1>
            <p class="text-sm text-slate-500 mb-8">Last updated: June 2026</p>
            <div class="space-y-6 text-slate-700 leading-relaxed">
                <h2 class="text-xl font-bold text-slate-900">1. Acceptance of Terms</h2>
                <p>By installing and using the FeedFixer app, you agree to be bound by these Terms of Service. If you do not agree, please do not use the service.</p>
                
                <h2 class="text-xl font-bold text-slate-900">2. Service Description</h2>
                <p>FeedFixer provides a tool to format and synchronize supplier CSV feeds for e-commerce platforms. The service is provided "as is" and we reserve the right to modify or discontinue features at any time.</p>
                
                <h2 class="text-xl font-bold text-slate-900">3. User Responsibilities</h2>
                <p>You are responsible for ensuring you have the legal right to use the supplier feeds you connect to FeedFixer. You agree not to use the service for any illegal or unauthorized purpose.</p>
                
                <h2 class="text-xl font-bold text-slate-900">4. Limitation of Liability</h2>
                <p>In no event shall FeedFixer be liable for any direct, indirect, incidental, or consequential damages, including loss of profits or data, arising from your use of the App.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
