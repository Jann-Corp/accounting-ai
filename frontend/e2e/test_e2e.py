"""
Python Playwright E2E tests for the accounting AI frontend.
Uses the backend venv Python which has playwright installed.
"""
import subprocess
import sys
import os

BACKEND_VENV_PY = '/home/l33klin/.hermes/profiles/coder/home/projects/accounting-ai/backend/venv/bin/python'
PROJ = '/home/l33klin/.hermes/profiles/coder/home/projects/accounting-ai/frontend'

PW_IMPORT = "from playwright.sync_api import sync_playwright\n\n"

def run_test(test_name, script_body):
    """Run a playwright Python script via temp file."""
    import tempfile
    script = PW_IMPORT + script_body
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [BACKEND_VENV_PY, tmp_path],
            capture_output=True, text=True, timeout=120,
            cwd=PROJ
        )
        if result.returncode != 0:
            print(f'FAIL: {test_name}')
            err = result.stderr
            out = result.stdout
            if out:
                # Print last 800 chars of stdout (contains assertion errors)
                print(out[-800:])
            if err:
                print(err[-400:])
            return False
        print(f'PASS: {test_name}')
        return True
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass


def test_login_page_loads():
    return run_test('test_login_page_loads', """
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000/login')
    assert 'AI记账' in page.locator('h1').first.inner_text()
    assert page.get_by_placeholder('请输入用户名').is_visible()
    assert page.get_by_placeholder('请输入密码').is_visible()
    browser.close()
""")


def test_unauthenticated_redirect():
    return run_test('test_unauthenticated_redirect', """
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000/')
    page.wait_for_url('**/login**', timeout=5000)
    browser.close()
""")


def test_register_and_login():
    import time
    ts = str(int(time.time() * 1000))
    return run_test('test_register_and_login', """
import time
ts = "%s"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000/login')
    page.get_by_role('button', name='立即注册').click()
    page.wait_for_timeout(500)
    page.get_by_placeholder('请输入用户名').fill('user' + ts)
    page.get_by_placeholder('请输入邮箱').fill('user' + ts + '@test.com')
    page.get_by_placeholder('请输入密码').fill('TestPass123!')
    page.get_by_role('button', name='注册').click()
    page.wait_for_timeout(2000)
    h1 = page.locator('h1:has-text("你好")').first.inner_text()
    assert '你好' in h1, 'Expected 你好 in h1, got: ' + h1
    browser.close()
""" % ts)


def test_navigation():
    import time
    ts = str(int(time.time() * 1000))
    return run_test('test_navigation', """
import time
ts = "%s"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000/login')
    page.get_by_role('button', name='立即注册').click()
    page.wait_for_timeout(300)
    page.get_by_placeholder('请输入用户名').fill('user' + ts)
    page.get_by_placeholder('请输入邮箱').fill('user' + ts + '@test.com')
    page.get_by_placeholder('请输入密码').fill('TestPass123!')
    page.get_by_role('button', name='注册').click()
    page.wait_for_timeout(2000)

    links = [
        ('记账', '/records'),
        ('AI识别', '/upload'),
        ('账户', '/wallets'),
        ('分类', '/categories'),
        ('统计', '/stats'),
    ]

    for label, suffix in links:
        page.get_by_role('link', name=label).first.dispatch_event('click')
        page.wait_for_timeout(500)
        page.wait_for_url('**' + suffix + '**', timeout=5000)

    browser.close()
""" % ts)


def test_create_wallet():
    import time
    ts = str(int(time.time() * 1000))
    return run_test('test_create_wallet', """
import time
ts = "%s"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000/login')
    page.get_by_role('button', name='立即注册').click()
    page.wait_for_timeout(300)
    page.get_by_placeholder('请输入用户名').fill('user' + ts)
    page.get_by_placeholder('请输入邮箱').fill('user' + ts + '@test.com')
    page.get_by_placeholder('请输入密码').fill('TestPass123!')
    page.get_by_role('button', name='注册').click()
    page.wait_for_timeout(2000)
    page.wait_for_timeout(500)

    page.get_by_role('link', name='账户').first.click()
    page.wait_for_url('**/wallets**', timeout=5000)
    page.get_by_role('button', name='+ 添加账户').click()
    page.wait_for_timeout(300)
    page.locator('#wallet-name').fill('我的银行卡')
    page.get_by_role('button', name='保存').click()
    page.wait_for_timeout(1000)
    assert page.get_by_text('我的银行卡').is_visible()
    browser.close()
""" % ts)


def test_categories():
    import time
    ts = str(int(time.time() * 1000))
    return run_test('test_categories', """
import time
ts = "%s"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    # Register & login
    page.goto('http://localhost:3000/login')
    page.get_by_role('button', name='立即注册').click()
    page.wait_for_timeout(300)
    page.get_by_placeholder('请输入用户名').fill('user' + ts)
    page.get_by_placeholder('请输入邮箱').fill('user' + ts + '@test.com')
    page.get_by_placeholder('请输入密码').fill('TestPass123!')
    page.get_by_role('button', name='注册').click()
    page.wait_for_timeout(2000)
    page.wait_for_timeout(500)

    # Navigate to categories
    page.get_by_role('link', name='分类').first.click()
    page.wait_for_url('**/categories**', timeout=5000)

    # Add a category
    page.get_by_role('button', name='+ 添加分类').click()
    page.wait_for_timeout(300)
    page.locator('input[type="text"]').first.fill('测试餐饮')
    page.get_by_role('button', name='保存').click()
    page.wait_for_timeout(1000)
    assert page.get_by_text('测试餐饮').is_visible(), 'Category not found after create'

    # Edit the category - click the edit button next to it
    category_card = page.locator('.bg-white.rounded-xl.shadow-sm', has_text='测试餐饮').first
    category_card.get_by_role('button', name='✏️').click()
    page.wait_for_timeout(300)
    page.locator('input[type="text"]').first.fill('测试餐饮v2')
    page.get_by_role('button', name='保存').click()
    page.wait_for_timeout(1000)
    assert page.get_by_text('测试餐饮v2').is_visible(), 'Category not found after edit'

    # Delete the category
    category_card2 = page.locator('.bg-white.rounded-xl.shadow-sm', has_text='测试餐饮v2').first
    # Dismiss confirm dialog
    page.on('dialog', lambda d: d.accept())
    category_card2.get_by_role('button', name='🗑️').click()
    page.wait_for_timeout(1000)

    browser.close()
""" % ts)


def test_records():
    import time
    ts = str(int(time.time() * 1000))
    return run_test('test_records', """
import time
ts = "%s"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    # Register & login
    page.goto('http://localhost:3000/login')
    page.get_by_role('button', name='立即注册').click()
    page.wait_for_timeout(300)
    page.get_by_placeholder('请输入用户名').fill('user' + ts)
    page.get_by_placeholder('请输入邮箱').fill('user' + ts + '@test.com')
    page.get_by_placeholder('请输入密码').fill('TestPass123!')
    page.get_by_role('button', name='注册').click()
    page.wait_for_timeout(2000)
    page.wait_for_timeout(500)

    # Add a wallet
    page.get_by_role('link', name='账户').first.click()
    page.wait_for_url('**/wallets**', timeout=5000)
    page.get_by_role('button', name='+ 添加账户').click()
    page.wait_for_timeout(300)
    page.locator('#wallet-name').fill('我的银行卡')
    page.get_by_role('button', name='保存').click()
    page.wait_for_timeout(1000)

    # Navigate to records
    page.get_by_role('link', name='记账').first.click()
    page.wait_for_url('**/records**', timeout=5000)

    # Add a record
    page.get_by_role('button', name='+ 添加记录').click()
    page.wait_for_timeout(300)
    # modal: inputs = [amount(number), note(text), date(datetime-local)]
    page.locator('input[type="number"]').first.fill('88.5')
    page.locator('input[type="text"]').first.fill('测试餐饮')
    page.get_by_role('button', name='保存').click()
    page.wait_for_timeout(1000)
    assert page.get_by_text('88.5').is_visible(), 'Record amount not found after create'

    # Edit the record
    record_row = page.locator('.bg-white.rounded-xl, .divide-y > div', has_text='88.5').first
    record_row.locator('button').first.click()
    page.wait_for_timeout(500)
    page.locator('input[type="number"]').first.fill('120.0')
    page.get_by_role('button', name='保存').click()
    page.wait_for_timeout(1000)
    assert page.get_by_text('120').first.is_visible(), 'Record amount not found after edit'

    browser.close()
""" % ts)


def test_stats():
    import time
    ts = str(int(time.time() * 1000))
    return run_test('test_stats', """
import time
ts = "%s"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    # Register & login
    page.goto('http://localhost:3000/login')
    page.get_by_role('button', name='立即注册').click()
    page.wait_for_timeout(300)
    page.get_by_placeholder('请输入用户名').fill('user' + ts)
    page.get_by_placeholder('请输入邮箱').fill('user' + ts + '@test.com')
    page.get_by_placeholder('请输入密码').fill('TestPass123!')
    page.get_by_role('button', name='注册').click()
    page.wait_for_timeout(2000)
    page.wait_for_timeout(500)

    # Navigate to stats
    page.get_by_role('link', name='统计').first.click()
    page.wait_for_url('**/stats**', timeout=5000)
    page.wait_for_timeout(1000)

    # Verify 4 summary cards are visible
    assert page.get_by_text('本月收入').is_visible(), '本月收入 card missing'
    assert page.get_by_text('本月支出').is_visible(), '本月支出 card missing'
    assert page.get_by_text('本月结余').is_visible(), '本月结余 card missing'
    assert page.get_by_text('记录数').is_visible(), '记录数 card missing'

    # Verify section headers
    assert page.get_by_text('支出分类').is_visible(), '支出分类 section missing'
    assert page.get_by_text('收支趋势').is_visible(), '收支趋势 section missing'

    # Test prev/next month navigation
    prev_btn = page.get_by_role('button', name='◀').first
    next_btn = page.get_by_role('button', name='▶').first
    prev_btn.click()
    page.wait_for_timeout(500)
    next_btn.click()
    page.wait_for_timeout(500)

    browser.close()
""" % ts)


def test_api_keys():
    import time
    ts = str(int(time.time() * 1000))
    return run_test('test_api_keys', r"""
import time
ts = "%s"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto('http://localhost:3000/login')
    page.get_by_role('button', name='立即注册').click()
    page.wait_for_timeout(500)
    page.get_by_placeholder('请输入用户名').fill('user' + ts)
    page.get_by_placeholder('请输入邮箱').fill('user' + ts + '@test.com')
    page.get_by_placeholder('请输入密码').fill('TestPass123!')
    page.get_by_role('button', name='注册').click()
    page.wait_for_timeout(3000)

    # Navigate to API Keys page
    page.evaluate("(function() { window.history.pushState({}, '', '/api-keys'); window.dispatchEvent(new PopStateEvent('popstate')); })()")
    page.wait_for_timeout(2000)

    # Verify page loaded
    page_inner = page.inner_text('body')
    assert 'API 密钥' in page_inner, 'Expected API Keys page, got: ' + page_inner[:300]

    # Verify modal opens when clicking + 新建 Key
    page.evaluate("(function() { var b=document.querySelectorAll('button'); for(var i=0;i<b.length;i++){if(b[i].textContent.trim().indexOf('+ 新建')>=0){b[i].click();break;}} })()")
    page.wait_for_timeout(1000)

    # Verify modal is open with required elements
    modal_text = page.inner_text('body')
    assert '新建 API Key' in modal_text, 'Modal did not open'
    assert 'Key 名称' in modal_text, 'Key name field missing'
    assert '过期时间' in modal_text, 'Expiry field missing'
    assert '取消' in modal_text, 'Cancel button missing'
    assert '创建' in modal_text, 'Create button missing'

    # Close modal
    page.locator('.fixed button', has_text='取消').click()
    page.wait_for_timeout(500)

    # Verify modal is closed
    assert '新建 API Key' not in page.inner_text('body')

    browser.close()
""" % ts)


if __name__ == '__main__':
    results = []

    print('\n=== Running E2E Tests ===\n')

    results.append(('test_login_page_loads', test_login_page_loads()))
    results.append(('test_unauthenticated_redirect', test_unauthenticated_redirect()))
    results.append(('test_register_and_login', test_register_and_login()))
    results.append(('test_navigation', test_navigation()))
    results.append(('test_create_wallet', test_create_wallet()))
    results.append(('test_categories', test_categories()))
    results.append(('test_records', test_records()))
    results.append(('test_stats', test_stats()))
    results.append(('test_api_keys', test_api_keys()))

    print('\n=== Results ===')
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        status = 'PASS' if ok else 'FAIL'
        print(f'  {status}: {name}')
    print(f'\nTotal: {passed}/{len(results)} passed')

    sys.exit(0 if passed == len(results) else 1)
