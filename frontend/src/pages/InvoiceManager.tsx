import { useState, useEffect, useCallback } from "react";

// ─── Theme tokens (matches Dashboard dark theme) ───────────────────────────────
const T = {
  bg:        "#0a0a0f",
  surface:   "#0f0f14",
  border:    "#1a1a1a",
  border2:   "#222",
  text:      "#f0f0f0",
  textSub:   "#888",
  textMuted: "#555",
  green:     "#1D9E75",
  greenBg:   "rgba(29,158,117,0.10)",
  red:       "#E24B4A",
  redBg:     "rgba(226,75,74,0.10)",
  yellow:    "#EF9F27",
  yellowBg:  "rgba(239,159,39,0.10)",
  blue:      "#4A90E2",
  blueBg:    "rgba(74,144,226,0.10)",
  purple:    "#9B59B6",
  purpleBg:  "rgba(155,89,182,0.10)",
};

// ─── Types ─────────────────────────────────────────────────────────────────────
interface Invoice {
  id: string;
  invoice_number: string;
  party_name: string;
  party_type: "customer" | "supplier";
  amount: number;
  paid_amount?: number;
  balance_due?: number;
  status: "paid" | "pending" | "overdue" | "draft" | "partial";
  due_date: string;
  invoice_date: string;
  description?: string;
  payment_link?: string;
  days_overdue?: number;
}

interface InvoiceFormData {
  invoice_number: string;
  party_name: string;
  party_type: "customer" | "supplier";
  amount: string;
  due_date: string;
  invoice_date: string;
  description: string;
}

interface SummaryStats {
  total_receivable: number;
  total_payable: number;
  overdue_amount: number;
  paid_this_month: number;
  overdue_count: number;
  pending_count: number;
}

// ─── API ───────────────────────────────────────────────────────────────────────
const API_BASE = "http://127.0.0.1:8000/v1";
const getAuthHeader = (): Record<string, string> => {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};
const apiFetch = async (path: string, options: RequestInit = {}) => {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...getAuthHeader(), ...(options.headers || {}) },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Network error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
};

// ─── Mock data (sirf jab API completely down ho) ───────────────────────────────
const MOCK_INVOICES: Invoice[] = [
  { id: "inv-001", invoice_number: "INV-2024-047", party_name: "Mehta Fabrics Pvt Ltd", party_type: "customer", amount: 500000, status: "paid", invoice_date: "2024-01-05", due_date: "2024-01-20" },
  { id: "inv-002", invoice_number: "INV-2024-048", party_name: "Gupta Traders", party_type: "customer", amount: 125000, status: "pending", invoice_date: "2024-01-10", due_date: "2024-02-10" },
];

const MOCK_STATS: SummaryStats = {
  total_receivable: 720000, total_payable: 225000, overdue_amount: 320000,
  paid_this_month: 545000, overdue_count: 1, pending_count: 3,
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (n: number) => n >= 100000 ? `₹${(n / 100000).toFixed(1)}L` : `₹${(n / 1000).toFixed(0)}K`;
const fmtFull = (n: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
const fmtDate = (s: string) => {
  if (!s) return "—";
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
};

// ✅ FIX 1: "partial" add kiya, Record<string, ...> taaki unknown status crash na kare
const STATUS: Record<string, { label: string; color: string; bg: string }> = {
  paid:    { label: "Paid",    color: T.green,   bg: T.greenBg },
  pending: { label: "Pending", color: T.yellow,  bg: T.yellowBg },
  overdue: { label: "Overdue", color: T.red,     bg: T.redBg },
  draft:   { label: "Draft",   color: T.textSub, bg: "rgba(136,136,136,0.10)" },
  partial: { label: "Partial", color: T.purple,  bg: T.purpleBg },
};

// ─── StatusBadge ──────────────────────────────────────────────────────────────
// ✅ FIX 2: unknown status ke liye fallback, crash nahi hoga
const StatusBadge = ({ status }: { status: string }) => {
  const s = STATUS[status] ?? { label: status, color: T.textSub, bg: "rgba(136,136,136,0.10)" };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 500, background: s.bg, color: s.color, whiteSpace: "nowrap" }}>
      <span style={{ width: 5, height: 5, borderRadius: "50%", background: s.color, flexShrink: 0 }} />
      {s.label}
    </span>
  );
};

// ─── StatCard ─────────────────────────────────────────────────────────────────
const StatCard = ({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent?: string }) => (
  <div style={{ background: T.surface, border: `0.5px solid ${T.border}`, borderRadius: 12, padding: "1rem 1.25rem" }}>
    <div style={{ fontSize: 10, color: T.textMuted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>{label}</div>
    <div style={{ fontSize: 22, fontWeight: 500, color: accent || T.text, lineHeight: 1.2 }}>{value}</div>
    {sub && <div style={{ fontSize: 11, color: T.textMuted, marginTop: 3 }}>{sub}</div>}
  </div>
);

// ─── Invoice Form Modal ───────────────────────────────────────────────────────
const InvoiceForm = ({ initial, onClose, onSave }: {
  initial?: Partial<Invoice>;
  onClose: () => void;
  onSave: (data: InvoiceFormData) => Promise<void>;
}) => {
  const today = new Date().toISOString().split("T")[0];
  const defaultDue = new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0];
  const [form, setForm] = useState<InvoiceFormData>({
    invoice_number: initial?.invoice_number || "",
    party_name: initial?.party_name || "",
    party_type: initial?.party_type || "customer",
    amount: initial?.amount?.toString() || "",
    due_date: initial?.due_date || defaultDue,
    invoice_date: initial?.invoice_date || today,
    description: initial?.description || "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const set = (k: keyof InvoiceFormData, v: string) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    if (!form.invoice_number || !form.party_name || !form.amount) {
      setError("Invoice number, party name aur amount required hai");
      return;
    }
    setSaving(true); setError(null);
    try { await onSave(form); onClose(); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "Save failed"); }
    finally { setSaving(false); }
  };

  const inp: React.CSSProperties = { width: "100%", boxSizing: "border-box", padding: "8px 12px", borderRadius: 8, border: `0.5px solid ${T.border2}`, background: T.bg, color: T.text, fontSize: 13, outline: "none" };
  const lbl: React.CSSProperties = { fontSize: 11, color: T.textMuted, marginBottom: 4, display: "block", textTransform: "uppercase", letterSpacing: "0.06em" };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: "1rem" }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background: T.surface, borderRadius: 14, border: `0.5px solid ${T.border2}`, padding: "1.5rem", width: "100%", maxWidth: 520, maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 500, color: T.text }}>{initial?.id ? "Invoice edit karo" : "Naya invoice banao"}</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: T.textSub, fontSize: 18, padding: 4 }}>✕</button>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label style={lbl}>Invoice type</label>
          <div style={{ display: "flex", gap: 8 }}>
            {(["customer", "supplier"] as const).map(t => (
              <button key={t} onClick={() => set("party_type", t)} style={{
                flex: 1, padding: "8px", borderRadius: 8,
                border: `${form.party_type === t ? "1.5px" : "0.5px"} solid ${form.party_type === t ? T.green : T.border2}`,
                background: form.party_type === t ? T.greenBg : "transparent",
                color: form.party_type === t ? T.green : T.textSub,
                fontWeight: form.party_type === t ? 500 : 400, cursor: "pointer", fontSize: 13,
              }}>
                {t === "customer" ? "📥 Customer (Receivable)" : "📤 Supplier (Payable)"}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div><label style={lbl}>Invoice number *</label><input style={inp} value={form.invoice_number} onChange={e => set("invoice_number", e.target.value)} placeholder="INV-2024-001" /></div>
          <div><label style={lbl}>Amount (₹) *</label><input style={inp} type="number" value={form.amount} onChange={e => set("amount", e.target.value)} placeholder="500000" /></div>
          <div style={{ gridColumn: "1 / -1" }}>
            <label style={lbl}>{form.party_type === "customer" ? "Customer ka naam *" : "Supplier ka naam *"}</label>
            <input style={inp} value={form.party_name} onChange={e => set("party_name", e.target.value)} placeholder={form.party_type === "customer" ? "Mehta Fabrics Pvt Ltd" : "Ramesh Yarn Suppliers"} />
          </div>
          <div><label style={lbl}>Invoice date</label><input style={inp} type="date" value={form.invoice_date} onChange={e => set("invoice_date", e.target.value)} /></div>
          <div><label style={lbl}>Due date</label><input style={inp} type="date" value={form.due_date} onChange={e => set("due_date", e.target.value)} /></div>
          <div style={{ gridColumn: "1 / -1" }}><label style={lbl}>Description</label><input style={inp} value={form.description} onChange={e => set("description", e.target.value)} placeholder="Cotton fabric supply — Jan batch" /></div>
        </div>

        {error && <div style={{ marginTop: "1rem", padding: "10px 12px", borderRadius: 8, background: T.redBg, color: T.red, fontSize: 12, border: `0.5px solid ${T.red}` }}>{error}</div>}

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: "1.5rem" }}>
          <button onClick={onClose} style={{ padding: "8px 20px", borderRadius: 8, border: `0.5px solid ${T.border2}`, background: "transparent", color: T.textSub, cursor: "pointer", fontSize: 13 }}>Cancel</button>
          <button onClick={handleSubmit} disabled={saving} style={{ padding: "8px 24px", borderRadius: 8, border: "none", background: saving ? T.border2 : T.text, color: T.bg, cursor: saving ? "not-allowed" : "pointer", fontSize: 13, fontWeight: 500 }}>
            {saving ? "Saving..." : initial?.id ? "Update karo" : "Banao"}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Invoice Row ──────────────────────────────────────────────────────────────
const InvoiceRow = ({ invoice, onEdit, onMarkPaid, onSendReminder, onGetPaymentLink }: {
  invoice: Invoice;
  onEdit: (inv: Invoice) => void;
  onMarkPaid: (id: string) => void;
  onSendReminder: (inv: Invoice) => void;
  onGetPaymentLink: (id: string) => void;
}) => {
  const [expanded, setExpanded] = useState(false);
  const isCustomer = invoice.party_type === "customer";

  const actionBtn = (label: string, onClick: () => void, color: string, bg: string) => (
    <button onClick={e => { e.stopPropagation(); onClick(); }} style={{ padding: "5px 12px", borderRadius: 6, border: `0.5px solid ${color}`, background: bg, color, cursor: "pointer", fontSize: 11, fontWeight: 500 }}>{label}</button>
  );

  const isPaid = invoice.status === "paid";

  return (
    <>
      <tr onClick={() => setExpanded(e => !e)} style={{ cursor: "pointer", borderBottom: `0.5px solid ${T.border}`, transition: "background 0.1s" }}
        onMouseEnter={e => (e.currentTarget.style.background = T.surface)}
        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
        <td style={{ padding: "12px 16px" }}>
          <div style={{ fontSize: 13, fontWeight: 500, color: T.text }}>{invoice.invoice_number}</div>
          <div style={{ fontSize: 11, color: T.textMuted, marginTop: 2 }}>{fmtDate(invoice.invoice_date)}</div>
        </td>
        <td style={{ padding: "12px 16px" }}>
          <div style={{ fontSize: 13, color: T.text }}>{invoice.party_name}</div>
          <div style={{ fontSize: 11, marginTop: 2, color: isCustomer ? T.blue : T.yellow, fontWeight: 500 }}>{isCustomer ? "↓ Receivable" : "↑ Payable"}</div>
        </td>
        <td style={{ padding: "12px 16px", textAlign: "right" }}>
          <div style={{ fontSize: 14, fontWeight: 500, color: isCustomer ? T.green : T.red }}>
            {isCustomer ? "+" : "-"}{fmtFull(invoice.amount)}
          </div>
          {/* ✅ Partial payment mein balance due bhi dikhao */}
          {invoice.status === "partial" && invoice.balance_due !== undefined && (
            <div style={{ fontSize: 11, color: T.purple, marginTop: 2 }}>
              Balance: {fmtFull(invoice.balance_due)}
            </div>
          )}
        </td>
        <td style={{ padding: "12px 16px", textAlign: "center" }}>
          <StatusBadge status={invoice.status} />
          {invoice.status === "overdue" && invoice.days_overdue ? (
            <div style={{ fontSize: 10, color: T.red, marginTop: 3, fontWeight: 500 }}>{invoice.days_overdue}d late</div>
          ) : null}
        </td>
        <td style={{ padding: "12px 16px", fontSize: 12, color: T.textSub, textAlign: "right" }}>{fmtDate(invoice.due_date)}</td>
        <td style={{ padding: "12px 8px", textAlign: "center" }}>
          <span style={{ fontSize: 12, color: T.textMuted, display: "inline-block", transform: expanded ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }}>▾</span>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={6} style={{ background: "rgba(255,255,255,0.02)", padding: "12px 16px", borderBottom: `0.5px solid ${T.border}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
              <div>
                {invoice.description && <p style={{ margin: "0 0 4px", fontSize: 12, color: T.textSub }}>{invoice.description}</p>}
                {invoice.status === "partial" && (
                  <p style={{ margin: "0 0 4px", fontSize: 12, color: T.purple }}>
                    Paid: {fmtFull(invoice.paid_amount ?? 0)} | Balance: {fmtFull(invoice.balance_due ?? 0)}
                  </p>
                )}
                <p style={{ margin: 0, fontSize: 11, color: T.textMuted }}>ID: {invoice.id}</p>
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {!isPaid && actionBtn("✓ Paid mark karo", () => onMarkPaid(invoice.id), T.green, T.greenBg)}
                {isCustomer && !isPaid && actionBtn("🔗 Payment link", () => onGetPaymentLink(invoice.id), T.blue, T.blueBg)}
                {invoice.status === "overdue" && actionBtn("📲 WhatsApp reminder", () => onSendReminder(invoice), T.yellow, T.yellowBg)}
                {actionBtn("✏️ Edit", () => onEdit(invoice), T.textSub, "rgba(136,136,136,0.08)")}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
export default function InvoiceManager() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [stats, setStats] = useState<SummaryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editInvoice, setEditInvoice] = useState<Invoice | undefined>();
  const [filter, setFilter] = useState<"all" | "customer" | "supplier">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | Invoice["status"]>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" | "info" } | null>(null);

  const showToast = (msg: string, type: "success" | "error" | "info" = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  // ✅ FIX 3: Real DB data use karo, mock sirf jab API completely down ho
  const loadData = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [invData, statsData] = await Promise.all([
        apiFetch("/invoices").catch(() => null),
        apiFetch("/invoices/summary").catch(() => null),
      ]);

      if (invData !== null) {
        // ✅ FIX 4: Backend fields → frontend fields map karo
        const mapped = (invData?.invoices ?? invData ?? []).map((inv: any) => ({
          ...inv,
          party_type: inv.invoice_type === "sales" ? "customer" : "supplier",
          amount: inv.total_amount,
          paid_amount: inv.paid_amount ?? 0,
          balance_due: inv.balance_due ?? 0,
          invoice_date: inv.invoice_date ?? inv.Invoice_date ?? "",
          due_date: inv.due_date ?? inv.Due_date ?? "",
        }));
        setInvoices(mapped);
      } else {
        setInvoices(MOCK_INVOICES);
        setError("API se connect nahi hua — demo data dikh raha hai");
      }

      if (statsData !== null) {
        setStats({
          total_receivable: statsData.receivables?.total_invoiced    ?? 0,
          total_payable:    statsData.payables?.total_payable        ?? 0,
          overdue_amount:   statsData.receivables?.overdue_amount    ?? 0,
          paid_this_month:  statsData.receivables?.total_collected   ?? 0,
          overdue_count:    statsData.receivables?.total_invoices    ?? 0,
          pending_count:    statsData.receivables?.total_invoices    ?? 0,
        });
      } else {
        setStats(MOCK_STATS);
      }

    } catch {
      setInvoices(MOCK_INVOICES);
      setStats(MOCK_STATS);
      setError("API se connect nahi hua — demo data dikh raha hai");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSave = async (data: InvoiceFormData) => {
    const payload = {
      business_id: "placeholder", // auth se aayega
      invoice_number: data.invoice_number,
      party_name: data.party_name,
      invoice_type: data.party_type === "customer" ? "sales" : "purchase",
      invoice_date: data.invoice_date,
      due_date: data.due_date,
      subtotal: parseFloat(data.amount),
      description: data.description,
    };

    await apiFetch("/invoices/create", { method: "POST", body: JSON.stringify(payload) }).catch(() => {
      setInvoices(prev => [{
        id: `inv-${Date.now()}`,
        invoice_number: data.invoice_number,
        party_name: data.party_name,
        party_type: data.party_type,
        amount: parseFloat(data.amount),
        status: "draft" as const,
        invoice_date: data.invoice_date,
        due_date: data.due_date,
        description: data.description,
      }, ...prev]);
    });

    showToast(editInvoice?.id ? "Invoice update ho gaya ✓" : "Naya invoice ban gaya ✓");
    setEditInvoice(undefined);
    loadData();
  };

  const handleMarkPaid = async (id: string) => {
    await apiFetch(`/invoices/${id}/mark-paid`, { method: "POST", body: JSON.stringify({ paid_amount: invoices.find(i => i.id === id)?.balance_due ?? invoices.find(i => i.id === id)?.amount, paid_date: new Date().toISOString().split("T")[0] }) }).catch(() => {
      setInvoices(prev => prev.map(inv => inv.id === id ? { ...inv, status: "paid" as const } : inv));
    });
    showToast("Payment mark ho gaya ✓");
    loadData();
  };

  const handleSendReminder = async (inv: Invoice) => {
    await apiFetch(`/invoices/${inv.id}/remind`, { method: "POST" }).catch(() => null);
    showToast(`WhatsApp reminder bheja — ${inv.party_name}`, "info");
  };

  const handleGetPaymentLink = async (id: string) => {
    try {
      const data = await apiFetch(`/payments/invoice/${id}/link`, { method: "POST" });
      if (data?.payment_link) {
        navigator.clipboard.writeText(data.payment_link).catch(() => null);
        showToast("Payment link copy ho gaya ✓");
      }
    } catch {
      showToast("Payment link generate nahi hua — try again", "error");
    }
  };

  const filtered = invoices.filter(inv => {
    const matchParty = filter === "all" || inv.party_type === filter;
    const matchStatus = statusFilter === "all" || inv.status === statusFilter;
    const matchSearch = !searchQuery || inv.party_name.toLowerCase().includes(searchQuery.toLowerCase()) || inv.invoice_number.toLowerCase().includes(searchQuery.toLowerCase());
    return matchParty && matchStatus && matchSearch;
  });

  const tab = (active: boolean, color = T.green): React.CSSProperties => ({
    padding: "5px 14px", borderRadius: 20, fontSize: 12, fontWeight: active ? 500 : 400, cursor: "pointer",
    border: `${active ? "1.5px" : "0.5px"} solid ${active ? color : T.border2}`,
    background: active ? `${color}1a` : "transparent", color: active ? color : T.textSub, transition: "all 0.15s",
  });

  const toastColor = toast?.type === "success" ? T.green : toast?.type === "error" ? T.red : T.blue;

  return (
    <div style={{ padding: "1.5rem", maxWidth: 1100, margin: "0 auto" }}>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 500, color: T.text }}>Invoice Manager</h1>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: T.textMuted }}>Apne sabhi receivables aur payables ek jagah</p>
        </div>
        <button onClick={() => { setEditInvoice(undefined); setShowForm(true); }}
          style={{ padding: "8px 18px", borderRadius: 8, border: "none", background: T.text, color: T.bg, cursor: "pointer", fontSize: 13, fontWeight: 500 }}>
          + Naya invoice
        </button>
      </div>

      {/* API Error */}
      {error && (
        <div style={{ marginBottom: "1rem", padding: "10px 14px", borderRadius: 8, background: T.yellowBg, color: T.yellow, fontSize: 12, border: `0.5px solid ${T.yellow}` }}>
          ⚠️ {error}
        </div>
      )}

      {/* Stats */}
      {stats && !loading && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 10, marginBottom: "1.5rem" }}>
          <StatCard label="Total receivable" value={fmt(stats.total_receivable)} sub={`${stats.pending_count} invoices`} accent={T.green} />
          <StatCard label="Total payable"    value={fmt(stats.total_payable)}    accent={T.red} />
          <StatCard label="Overdue"          value={fmt(stats.overdue_amount)}   sub={`${stats.overdue_count} invoice`} accent={T.red} />
          <StatCard label="Total collected"  value={fmt(stats.paid_this_month)}  accent={T.green} />
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center", marginBottom: "1rem" }}>
        <div style={{ position: "relative", flex: "1 1 200px", maxWidth: 280 }}>
          <span style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: T.textMuted, fontSize: 13 }}>🔍</span>
          <input style={{ width: "100%", boxSizing: "border-box", padding: "7px 12px 7px 30px", borderRadius: 8, border: `0.5px solid ${T.border2}`, background: T.bg, color: T.text, fontSize: 12, outline: "none" }}
            placeholder="Party name ya invoice no..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        </div>

        <div style={{ display: "flex", gap: 6 }}>
          {(["all", "customer", "supplier"] as const).map(t => (
            <button key={t} onClick={() => setFilter(t)} style={tab(filter === t, t === "supplier" ? T.yellow : T.green)}>
              {t === "all" ? "Sab" : t === "customer" ? "↓ Receivable" : "↑ Payable"}
            </button>
          ))}
        </div>

        {/* ✅ FIX 5: Partial option bhi add kiya status filter mein */}
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value as typeof statusFilter)}
          style={{ padding: "5px 10px", borderRadius: 8, border: `0.5px solid ${T.border2}`, background: T.bg, color: T.textSub, fontSize: 12, cursor: "pointer", outline: "none" }}>
          <option value="all">Sabhi status</option>
          <option value="pending">Pending</option>
          <option value="overdue">Overdue</option>
          <option value="partial">Partial</option>
          <option value="paid">Paid</option>
          <option value="draft">Draft</option>
        </select>

        <span style={{ fontSize: 11, color: T.textMuted, marginLeft: "auto" }}>{filtered.length} invoice</span>
      </div>

      {/* Table */}
      <div style={{ background: T.surface, borderRadius: 12, border: `0.5px solid ${T.border}`, overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: "3rem", textAlign: "center", color: T.textMuted, fontSize: 13 }}>Loading invoices...</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: "3rem", textAlign: "center", color: T.textMuted }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📄</div>
            <div style={{ fontSize: 14, marginBottom: 4, color: T.textSub }}>Koi invoice nahi mila</div>
            <div style={{ fontSize: 12 }}>Filter change karo ya naya invoice banao</div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
              <thead>
                <tr style={{ borderBottom: `0.5px solid ${T.border}`, background: "rgba(255,255,255,0.02)" }}>
                  {[{ l: "Invoice #", w: "17%" }, { l: "Party", w: "28%" }, { l: "Amount", w: "17%", a: "right" }, { l: "Status", w: "14%", a: "center" }, { l: "Due date", w: "14%", a: "right" }, { l: "", w: "6%" }].map((col, i) => (
                    <th key={i} style={{ padding: "10px 16px", fontSize: 10, fontWeight: 500, color: T.textMuted, textAlign: (col.a as React.CSSProperties["textAlign"]) || "left", textTransform: "uppercase", letterSpacing: "0.06em", width: col.w }}>{col.l}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(inv => (
                  <InvoiceRow key={inv.id} invoice={inv}
                    onEdit={i => { setEditInvoice(i); setShowForm(true); }}
                    onMarkPaid={handleMarkPaid}
                    onSendReminder={handleSendReminder}
                    onGetPaymentLink={handleGetPaymentLink}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Overdue alert */}
      {stats && stats.overdue_count > 0 && (
        <div style={{ marginTop: "1rem", padding: "12px 16px", borderRadius: 10, background: T.redBg, border: `0.5px solid ${T.red}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <span style={{ fontSize: 13, fontWeight: 500, color: T.red }}>⚠️ {stats.overdue_count} overdue invoice — {fmt(stats.overdue_amount)} outstanding</span>
            <span style={{ fontSize: 11, color: T.red, marginLeft: 8, opacity: 0.7 }}>Yeh tumhara credit score affect kar raha hai</span>
          </div>
          <button onClick={() => setStatusFilter("overdue")} style={{ padding: "5px 12px", borderRadius: 6, border: `0.5px solid ${T.red}`, background: "transparent", color: T.red, cursor: "pointer", fontSize: 12, fontWeight: 500 }}>Dekho</button>
        </div>
      )}

      {showForm && <InvoiceForm initial={editInvoice} onClose={() => { setShowForm(false); setEditInvoice(undefined); }} onSave={handleSave} />}

      {toast && (
        <div style={{ position: "fixed", bottom: 24, right: 24, padding: "11px 18px", borderRadius: 10, background: `${toastColor}18`, color: toastColor, border: `0.5px solid ${toastColor}`, fontSize: 13, fontWeight: 500, zIndex: 2000, boxShadow: "0 4px 20px rgba(0,0,0,0.3)" }}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}