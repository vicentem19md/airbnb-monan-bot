import os
import json
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from data_manager import DataManager

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ALLOWED_USER = os.environ.get("ALLOWED_USER_ID")  # tu ID de Telegram

dm = DataManager()

# ── COMANDOS ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 *Bot Airbnb activo*\n\n"
        "Comandos disponibles:\n\n"
        "📥 *RESERVAS:*\n"
        "`/reserva ENTRADA SALIDA PLATAFORMA TARIFA`\n"
        "Ej: `/reserva 05/01 10/01 Airbnb 90`\n\n"
        "💸 *GASTOS:*\n"
        "`/gasto CATEGORIA DESCRIPCION MONTO`\n"
        "Ej: `/gasto Limpieza \"Limpieza profunda\" 45`\n\n"
        "📊 *REPORTES:*\n"
        "`/resumen` — Ver resumen del mes actual\n"
        "`/mes NOMBRE` — Ver resumen de un mes\n"
        "`/kpis` — Ver KPIs del año\n\n"
        "📋 *OTROS:*\n"
        "`/ultimas` — Ver últimas 5 entradas\n"
        "`/exportar` — Descargar Excel actualizado",
        parse_mode="Markdown"
    )

async def agregar_reserva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text(
                "❌ Formato incorrecto.\n"
                "Usa: `/reserva ENTRADA SALIDA PLATAFORMA TARIFA`\n"
                "Ej: `/reserva 05/01 10/01 Airbnb 90`",
                parse_mode="Markdown"
            )
            return
        
        entrada = args[0]   # "05/01"
        salida  = args[1]   # "10/01"
        plataforma = args[2]  # "Airbnb"
        tarifa = float(args[3])
        huesped = " ".join(args[4:]) if len(args) > 4 else "Sin nombre"
        
        resultado = dm.agregar_reserva(entrada, salida, plataforma, tarifa, huesped)
        
        await update.message.reply_text(
            f"✅ *Reserva registrada*\n\n"
            f"📅 {resultado['entrada']} → {resultado['salida']}\n"
            f"🌙 Noches: *{resultado['noches']}*\n"
            f"📱 Plataforma: {plataforma}\n"
            f"💵 Tarifa/noche: ${tarifa:.2f}\n"
            f"💰 Ingreso bruto: *${resultado['bruto']:.2f}*\n"
            f"📉 Comisión ({resultado['com_pct']}%): -${resultado['comision']:.2f}\n"
            f"✨ Ingreso neto: *${resultado['neto']:.2f}*",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\nRevisa el formato e intenta de nuevo.")

async def agregar_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "❌ Formato incorrecto.\n"
                "Usa: `/gasto CATEGORIA DESCRIPCION MONTO`\n"
                "Ej: `/gasto Limpieza \"Limpieza x2\" 45`",
                parse_mode="Markdown"
            )
            return
        
        categoria = args[0]
        monto = float(args[-1])
        descripcion = " ".join(args[1:-1]).strip('"')
        
        resultado = dm.agregar_gasto(categoria, descripcion, monto)
        
        await update.message.reply_text(
            f"✅ *Gasto registrado*\n\n"
            f"📂 Categoría: {categoria}\n"
            f"📝 Descripción: {descripcion}\n"
            f"💸 Monto: *${monto:.2f}*\n"
            f"📅 Fecha: {resultado['fecha']}\n"
            f"📊 Total gastos este mes: *${resultado['total_mes']:.2f}*",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def resumen_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    
    if context.args:
        mes_nombre = context.args[0].capitalize()
    else:
        mes_nombre = datetime.datetime.now().strftime("%B")
    
    r = dm.resumen_mes(mes_nombre)
    
    utilidad_emoji = "✅" if r['utilidad'] >= 0 else "🚨"
    ocup_emoji = "🟢" if r['ocupacion'] >= 0.65 else ("🟡" if r['ocupacion'] >= 0.4 else "🔴")
    
    await update.message.reply_text(
        f"📊 *Resumen — {mes_nombre}*\n"
        f"{'─'*28}\n"
        f"🌙 Noches reservadas: *{r['noches']}*\n"
        f"📋 Reservas: *{r['num_reservas']}*\n"
        f"{ocup_emoji} Ocupación: *{r['ocupacion']*100:.1f}%*\n\n"
        f"💵 Ingreso bruto: *${r['bruto']:.2f}*\n"
        f"📉 Comisiones: -${r['comisiones']:.2f}\n"
        f"💰 Ingreso neto: *${r['neto']:.2f}*\n\n"
        f"🏷️ Gastos fijos: ${r['fijos']:.2f}\n"
        f"🔄 Gastos variables: ${r['variables']:.2f}\n"
        f"📉 Total gastos: *${r['gastos']:.2f}*\n\n"
        f"{utilidad_emoji} *Utilidad neta: ${r['utilidad']:.2f}*\n"
        f"📈 Margen: *{r['margen']*100:.1f}%*\n"
        f"💲 ADR: *${r['adr']:.2f}/noche*",
        parse_mode="Markdown"
    )

async def ver_kpis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    
    k = dm.kpis_anuales()
    roi_emoji = "🚀" if k['roi'] > 0.1 else ("✅" if k['roi'] > 0 else "🚨")
    
    await update.message.reply_text(
        f"📈 *KPIs del Año {datetime.datetime.now().year}*\n"
        f"{'─'*28}\n"
        f"🌙 Total noches: *{k['noches_total']}*\n"
        f"🏠 Ocupación anual: *{k['ocupacion']*100:.1f}%*\n"
        f"💲 ADR promedio: *${k['adr']:.2f}*\n"
        f"📊 RevPAR: *${k['revpar']:.2f}*\n\n"
        f"💰 Ingreso neto: *${k['ingreso_neto']:.2f}*\n"
        f"📉 Total gastos: *${k['gastos']:.2f}*\n"
        f"✨ Utilidad neta: *${k['utilidad']:.2f}*\n\n"
        f"{roi_emoji} ROI estimado: *{k['roi']*100:.1f}%*\n"
        f"⏱️ Payback: *{k['payback']:.1f} meses*",
        parse_mode="Markdown"
    )

async def exportar_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    await update.message.reply_text("⏳ Generando Excel actualizado...")
    
    ruta = dm.exportar_excel()
    
    with open(ruta, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=f"Airbnb_Reporte_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            caption="📊 Excel actualizado con todos tus datos."
        )

async def ultimas_entradas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    
    entradas = dm.ultimas_entradas(5)
    texto = "📋 *Últimas 5 entradas:*\n\n"
    for e in entradas:
        texto += f"{'🏨' if e['tipo']=='reserva' else '💸'} {e['resumen']}\n"
    
    await update.message.reply_text(texto, parse_mode="Markdown")

async def verificar_usuario(update: Update) -> bool:
    if ALLOWED_USER and str(update.effective_user.id) != ALLOWED_USER:
        await update.message.reply_text("⛔ No tienes permiso para usar este bot.")
        return False
    return True

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reserva", agregar_reserva))
    app.add_handler(CommandHandler("gasto", agregar_gasto))
    app.add_handler(CommandHandler("resumen", resumen_mes))
    app.add_handler(CommandHandler("mes", resumen_mes))
    app.add_handler(CommandHandler("kpis", ver_kpis))
    app.add_handler(CommandHandler("exportar", exportar_excel))
    app.add_handler(CommandHandler("ultimas", ultimas_entradas))
    
    print("Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
