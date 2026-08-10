import pytest
from src.execution.mock_env import MockPerpetualEnv, DisqualificationException

def test_initial_state():
    env = MockPerpetualEnv()
    assert env.wallet_balance == 100000.0
    assert env.leverage == 5.0
    assert env.commission_rate == 0.0002
    assert env.get_account_equity() == 100000.0
    assert env.get_nav() == 1.0
    assert env.position_size == 0.0

def test_set_leverage():
    env = MockPerpetualEnv()
    env.set_leverage(10.0)
    assert env.leverage == 10.0

    with pytest.raises(ValueError):
        env.set_leverage(0)

    with pytest.raises(ValueError):
        env.set_leverage(-5.0)

def test_transaction_costs_and_slippage():
    env = MockPerpetualEnv(initial_balance=100000.0, commission_rate=0.0002)
    # Trade 1 BTC at 50000 with 10 slippage
    # Long trade => execution_price = 50000 + 10 = 50010
    # trade_value = 1 * 50010 = 50010
    # commission = 50010 * 0.0002 = 10.002
    res = env.execute_trade(size=1.0, price=50000.0, slippage=10.0)

    assert res["execution_price"] == 50010.0
    assert res["commission"] == 10.002
    assert res["slippage_loss"] == 10.0
    assert res["new_position_size"] == 1.0
    assert res["new_entry_price"] == 50010.0

    assert env.wallet_balance == 100000.0 - 10.002

    # Update price back to 50000
    # unrealized_pnl = 1.0 * (50000 - 50010) = -10
    env.update_price(50000.0)
    assert env.get_unrealized_pnl() == -10.0
    assert env.get_account_equity() == 100000.0 - 10.002 - 10.0

def test_strict_disqualification_guard_equity():
    env = MockPerpetualEnv(initial_balance=100000.0)
    # Trade 100 BTC at 1000
    env.execute_trade(size=100.0, price=1000.0)

    # Drop price significantly
    # Position: 100 long at 1000
    # Eq = 100000 - comm + PnL
    # To hit 800 Eq, PnL approx -99200
    # 100 * (current - 1000) = -99200 => current = 1000 - 992 = 8

    # This should trigger DisqualificationException
    with pytest.raises(DisqualificationException) as exc_info:
        env.update_price(5.0)

    assert "dropped below 800" in str(exc_info.value) or "dropped below 0.8" in str(exc_info.value)

def test_strict_disqualification_guard_nav():
    env = MockPerpetualEnv(initial_balance=100000.0)
    # Trade 10 BTC at 50000
    env.execute_trade(size=10.0, price=50000.0)

    # Drop price to trigger NAV < 0.8
    # NAV = Eq / 100000. To reach NAV < 0.8, Eq < 80000
    # Eq = 100000 - comm + PnL
    # PnL approx -20000 => 10 * (current - 50000) = -20000 => current - 50000 = -2000 => current = 48000

    with pytest.raises(DisqualificationException) as exc_info:
        env.update_price(47000.0)

    assert "dropped below 0.8" in str(exc_info.value)

def test_short_position_profit():
    env = MockPerpetualEnv(initial_balance=100000.0)
    # Short 1 BTC at 50000
    env.execute_trade(size=-1.0, price=50000.0)
    assert env.position_size == -1.0

    # Price drops to 40000
    env.update_price(40000.0)
    # unrealized pnl = -1.0 * (40000 - 50000) = 10000
    assert env.get_unrealized_pnl() == 10000.0

    # Close position
    res = env.execute_trade(size=1.0, price=40000.0)
    assert res["realized_pnl"] == 10000.0
    assert env.position_size == 0.0

def test_maintenance_margin_and_margin_balance():
    env = MockPerpetualEnv(initial_balance=100000.0, maintenance_margin_rate=0.005)
    env.execute_trade(size=2.0, price=50000.0)

    margin_balance = env.get_margin_balance()
    maintenance_margin = env.get_maintenance_margin()

    # Commission = 2 * 50000 * 0.0002 = 20
    # Eq = 100000 - 20 = 99980
    assert margin_balance == 99980.0
    # Maint margin = position_value * rate = (2 * 50000) * 0.005 = 100000 * 0.005 = 500
    assert maintenance_margin == 500.0
