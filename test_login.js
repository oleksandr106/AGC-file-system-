const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({headless: true});
    const page = await browser.newPage();
    
    // Capture console errors
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.log('PAGE ERROR:', msg.text());
        }
    });
    
    page.on('pageerror', err => {
        console.log('PAGE EXCEPTION:', err.toString());
    });

    try {
        await page.goto('http://localhost:8000', {waitUntil: 'networkidle0'});
        console.log('Page loaded');
        
        // Wait for login screen to be visible
        await page.waitForSelector('#username', {visible: true, timeout: 5000});
        console.log('Login screen visible');
        
        // Type credentials
        await page.type('#username', 'admin');
        await page.type('#password', 'admin123');
        
        // Click login
        await page.click('.login-btn');
        console.log('Clicked login');
        
        // Wait 3 seconds
        await new Promise(r => setTimeout(r, 3000));
        
        // Check what is visible
        const loginDisplay = await page.$eval('#loginScreen', el => window.getComputedStyle(el).display);
        const appDisplay = await page.$eval('#appScreen', el => window.getComputedStyle(el).display);
        
        console.log('Login display:', loginDisplay);
        console.log('App display:', appDisplay);
        
    } catch (e) {
        console.error('Test failed:', e);
    } finally {
        await browser.close();
    }
})();
