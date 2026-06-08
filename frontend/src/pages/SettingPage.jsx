import { useEffect, useState } from "react";
import { getOrganizationSettings, updateOrganizationSettings } from "../lib/api";


export default function SettingPage() {
    const [settings, setSettings] = useState(null);
    const [brandVoice, setBrandVoice] = useState("");
    const [executionMode, setExecutionMode] = useState("rules_based");
    const [fromEmail, setFromEmail] = useState("");
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        async function fetchSettings() {
            try{
                const data = await getOrganizationSettings();
                setSettings(data);
                setBrandVoice(data.brand_voice || "");
                setExecutionMode(data.sender_settings?.execution_mode || "rules_based");
                setFromEmail(data.sender_settings?.from_email || "");
            }catch(error) {
                console.error("Failed to load settings:", error);
            }
        }
        fetchSettings();
    }, [])

    const handleSave = async () => {
        setIsSaving(true);
        await updateOrganizationSettings({
          brand_voice: brandVoice,
          sender_settings: {
            ...settings?.sender_settings,
            execution_mode: executionMode,
            from_email: fromEmail,
          },
        });
        setIsSaving(false);
        alert("Settings saved successfully!");
      };
    

    if (!settings) return <div className="p-8">Loading settings...</div>;

    return (
        <div className="p-8 max-w-4xl">
          <h1 className="text-3xl font-bold mb-8">Organization Settings</h1>
          <div className="surface mb-8" style={{ padding: "1.5rem" }}>
            <h2 className="text-xl font-semibold mb-4">AI Execution Mode</h2>
            <select
              value={executionMode}
              onChange={(e) => setExecutionMode(e.target.value)}
              className="w-full p-2 border rounded-md mb-2"
            >
              <option value="rules_based">Safety Engine (Auto-send low risk, hold high risk)</option>
              <option value="manual">100% Manual (Require human approval for everything)</option>
              <option value="automatic">100% Automatic (Let the AI run wild - Not Recommended)</option>
            </select>
            <p className="text-sm text-gray-500">Determines how autonomously the AI operates.</p>
          </div>
          <div className="surface mb-8" style={{ padding: "1.5rem" }}>
            <h2 className="text-xl font-semibold mb-4">Email Configuration</h2>
            <label className="block text-sm font-medium mb-1">Fallback 'From' Email Address</label>
            <input
              type="email"
              value={fromEmail}
              onChange={(e) => setFromEmail(e.target.value)}
              className="w-full p-2 border rounded-md"
              placeholder="sales@yourcompany.com"
            />
          </div>
          <div className="surface mb-8" style={{ padding: "1.5rem" }}>
            <h2 className="text-xl font-semibold mb-4">Brand Voice Training</h2>
            <p className="text-sm text-gray-500 mb-4">
              Tell the AI exactly how it should sound. The LLM will strictly adhere to these instructions.
            </p>
            <textarea
              value={brandVoice}
              onChange={(e) => setBrandVoice(e.target.value)}
              className="w-full p-4 border rounded-md font-mono text-sm"
              rows="8"
              placeholder="e.g., Keep sentences extremely short. Never use exclamation marks. Sound authoritative but approachable. Don't use buzzwords."
            />
          </div>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
          >
            {isSaving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      );
}
