import os
import json
import datetime
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from data_manager import DataManager

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ALLOWED_USER = os.environ.get("ALLOWED_USER_ID")

dm = DataManager()

async def verificar_usuario(update: Update) -> bool:
    if ALLOWED_USER and str(update.effective_user.id) != str(ALLOWED_USER):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 Bot Airbnb activo\n\n"
        "Comandos disponibles:\n\n"
        "RESERVAS:\n"
        "/reserva ENTRADA SALIDA PLATAFORMA TARIFA\n"
        "Ej: /reserva 05/01 10/01 Airbnb 90\n\n"
        "GASTOS:\n"
        "/gasto CATEGORIA DESCRIPCION MONTO\n"
        "Ej: /gasto Limpieza Limpieza-post-huesped 45\n\n"
        "REPORTES:\n"
        "/resumen — Resumen del mes actual\n"
        "/kpis — KPIs del año\n"
        "/ultimas — Ultimas 5 entradas\n"
        "/exportar — Descargar Excel"
    )

async def agregar_reserva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text(
                "Formato: /reserva ENTRADA SALIDA PLATAFORMA TARIFA\n"
                "Ej: /reserva 05/01 10/01 Airbnb 90"
            )
            return
        entrada, salida, plataforma, tarifa = args[0], args[1], args[2], float(args[3])
        huesped = " ".join(args[4:]) if len(args) > 4 else "Sin nombre"
        r = dm.agregar_reserva(entrada, salida, plataforma, tarifa, huesped)
        await update.message.reply_text(
            f"Reserva registrada\n"
            f"Fechas: {r['entrada']} al {r['salida']}\n"
            f"Noches: {r['noches']}\n"
            f"Plataforma: {plataforma}\n"
            f"Ingreso bruto: ${r['bruto']:.2f}\n"
            f"Comision ({r['com_pct']}%): -${r['comision']:.2f}\n"
            f"Ingreso neto: ${r['neto']:.2f}"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def agregar_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "Formato: /gasto CATEGORIA DESCRIPCION MONTO\n"
                "Ej: /gasto Limpieza Limpieza-general 45"
            )
            return
        categoria = args[0]
        monto = float(args[-1])
        descripcion = " ".join(args[1:-1]).replace("-", " ")
        r = dm.agregar_gasto(categoria, descripcion, monto)
        await update.message.reply_text(
            f"Gasto registrado\n"
            f"Categoria: {categoria}\n"
            f"Descripcion: {descripcion}\n"
            f"Monto: ${monto:.2f}\n"
            f"Fecha: {r['fecha']}\n"
            f"Total gastos este mes: ${r['total_mes']:.2f}"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def resumen_mes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    if context.args:
        mes_nombre = context.args[0].capitalize()
    else:
        meses = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
                 7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}
        mes_nombre = meses[datetime.datetime.now().month]
    r = dm.resumen_mes(mes_nombre)
    await update.message.reply_text(
        f"Resumen {mes_nombre}\n"
        f"Noches reservadas: {r['noches']}\n"
        f"Numero de reservas: {r['num_reservas']}\n"
        f"Ocupacion: {r['ocupacion']*100:.1f}%\n\n"
        f"Ingreso bruto: ${r['bruto']:.2f}\n"
        f"Comisiones: -${r['comisiones']:.2f}\n"
        f"Ingreso neto: ${r['neto']:.2f}\n\n"
        f"Gastos fijos: ${r['fijos']:.2f}\n"
        f"Gastos variables: ${r['variables']:.2f}\n"
        f"Total gastos: ${r['gastos']:.2f}\n\n"
        f"UTILIDAD NETA: ${r['utilidad']:.2f}\n"
        f"Margen: {r['margen']*100:.1f}%\n"
        f"ADR: ${r['adr']:.2f}/noche"
    )

async def ver_kpis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    k = dm.kpis_anuales()
    await update.message.reply_text(
        f"KPIs del Año {datetime.datetime.now().year}\n"
        f"Total noches: {k['noches_total']}\n"
        f"Ocupacion anual: {k['ocupacion']*100:.1f}%\n"
        f"ADR promedio: ${k['adr']:.2f}\n"
        f"RevPAR: ${k['revpar']:.2f}\n\n"
        f"Ingreso neto: ${k['ingreso_neto']:.2f}\n"
        f"Total gastos: ${k['gastos']:.2f}\n"
        f"Utilidad neta: ${k['utilidad']:.2f}\n\n"
        f"ROI estimado: {k['roi']*100:.1f}%\n"
        f"Payback: {k['payback']:.1f} meses"
    )

async def exportar_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    await update.message.reply_text("Generando Excel...")
    ruta = dm.exportar_excel()
    with open(ruta, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=f"Airbnb_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            caption="Excel actualizado con todos tus datos."
        )

async def ultimas_entradas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await verificar_usuario(update): return
    entradas = dm.ultimas_entradas(5)
    texto = "Ultimas 5 entradas:\n\n"
    for e in entradas:
        icono = "🏨" if e['tipo'] == 'reserva' else "💸"
        texto += f"{icono} {e['resumen']}\n"
    await update.message.reply_text(texto)

def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN no esta configurado en las variables de entorno")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reserva", agregar_reserva))
    app.add_handler(CommandHandler("gasto", agregar_gasto))
    app.add_handler(CommandHandler("resumen", resumen_mes))
    app.add_handler(CommandHandler("mes", resumen_mes))
    app.add_handler(CommandHandler("kpis", ver_kpis))
    app.add_handler(CommandHandler("exportar", exportar_excel))
    app.add_handler(CommandHandler("ultimas", ultimas_entradas))
    
    print("Bot iniciado correctamente")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
