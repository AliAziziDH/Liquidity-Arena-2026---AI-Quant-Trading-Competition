import subprocess
import json
from typing import Dict, Any, Optional

class LiveExecutor:
    """
    Interfaces with the RapidX CLI to perform live trading execution.
    Replaces MockPerpetualEnv for production environments.
    """
    def __init__(self, symbol: str = "BINANCE_PERP_BTC_USDT"):
        self.symbol = symbol

    def _run_rapidx_command(self, *args) -> Dict[str, Any]:
        """Runs a rapidx CLI command and parses the JSON output."""
        cmd = ["rapidx"] + list(args) + ["--json"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            # rapidx returns non-zero on failure? According to docs, it returns {"ok": false} on stdout mostly.
            # but just in case:
            try:
                return json.loads(e.stdout)
            except json.JSONDecodeError:
                raise RuntimeError(f"RapidX CLI error (exit code {e.returncode}): {e.stderr}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse RapidX JSON output: {e}")

    def get_ticker(self) -> Dict[str, Any]:
        """Gets current ticker info."""
        payload = json.dumps({"symbol": self.symbol})
        return self._run_rapidx_command("market", "get-ticker", "--input", payload)

    def get_portfolio_overview(self) -> Dict[str, Any]:
        """Gets current portfolio equity, margin, etc."""
        return self._run_rapidx_command("portfolio", "overview")

    def get_position(self) -> Dict[str, Any]:
        """Gets current position for the symbol."""
        # 'rapidx position query --json' returns all positions? Or we need to parse it?
        # Let's assume it returns a list of positions or an object.
        return self._run_rapidx_command("position", "query")

    def execute_trade(self, size_diff: float, max_notional: float, client_order_id: str, current_position: float = 0.0) -> Optional[Dict[str, Any]]:
        """
        Executes a trade via preview-then-submit flow.
        size_diff > 0 for BUY, size_diff < 0 for SELL.
        """
        if abs(size_diff) < 1e-6:
            return None # No meaningful trade size

        side = "BUY" if size_diff > 0 else "SELL"
        quantity = str(abs(size_diff))

        # Determine positionSide accurately for Hedge Mode
        # If we are long (current_position > 0) and we sell, we are reducing LONG
        # If we are short (current_position < 0) and we buy, we are reducing SHORT
        # If we are flat (current_position == 0) and buy, we open LONG. If sell, open SHORT.
        if current_position > 0:
             position_side = "LONG"
        elif current_position < 0:
             position_side = "SHORT"
        else:
             position_side = "LONG" if side == "BUY" else "SHORT"

        preview_input = {
            "symbol": self.symbol,
            "side": side,
            "positionSide": position_side,
            "orderType": "MARKET",
            "quantity": quantity,
            "maxNotional": str(max_notional),
            "clientOrderId": client_order_id
        }

        preview_res = self._run_rapidx_command("order", "place-preview", "--input", json.dumps(preview_input))

        if not preview_res.get("ok"):
            print(f"Order preview failed: {preview_res}")
            return None

        # Extract preview tokens
        preview_data = preview_res.get("data", {})
        preview_id = preview_data.get("previewId")
        continue_consent_id = preview_data.get("confirmation", {}).get("submitToken")

        if not preview_id or not continue_consent_id:
             # Depending on schema, previewId might be at top level
             preview_id = preview_res.get("previewId", preview_id)
             continue_consent_id = preview_res.get("confirmation", {}).get("submitToken", continue_consent_id)
             if not preview_id or not continue_consent_id:
                 print(f"Could not extract preview tokens from: {preview_res}")
                 return None

        submit_input = preview_input.copy()
        submit_input["previewId"] = preview_id
        submit_input["continueConsentId"] = continue_consent_id

        submit_res = self._run_rapidx_command("order", "place", "--input", json.dumps(submit_input))
        return submit_res
