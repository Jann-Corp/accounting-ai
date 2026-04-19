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
            if err:
                print(err[:400])
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
    page.wait_for_url('http://localhost:3000/', timeout=10000)
    page.wait_for_selector('h1:has-text("你好")', timeout=5000)
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
    page.wait_for_url('http://localhost:3000/', timeout=10000)

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
    page.wait_for_url('http://localhost:3000/', timeout=10000)

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


if __name__ == '__main__':
    results = []

    print('\n=== Running E2E Tests ===\n')

    results.append(('test_login_page_loads', test_login_page_loads()))
    results.append(('test_unauthenticated_redirect', test_unauthenticated_redirect()))
    results.append(('test_register_and_login', test_register_and_login()))
    results.append(('test_navigation', test_navigation()))
    results.append(('test_create_wallet', test_create_wallet()))

    print('\n=== Results ===')
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        status = 'PASS' if ok else 'FAIL'
        print(f'  {status}: {name}')
    print(f'\nTotal: {passed}/{len(results)} passed')

    sys.exit(0 if passed == len(results) else 1)
