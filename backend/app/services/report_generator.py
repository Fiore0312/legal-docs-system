from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json
from datetime import datetime
import logging
from ..models.documento import Documento, DocumentType

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
        self.plots_dir = Path("plots")
        self.plots_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Stili custom
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        ))
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10
        ))

    async def generate_pdf_report(
        self,
        results: List[Dict[str, Any]],
        include_stats: bool = True,
        include_content: bool = False
    ) -> Path:
        """
        Genera un report PDF completo con statistiche e visualizzazioni.
        """
        try:
            # Genera nome file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.export_dir / f"report_{timestamp}.pdf"
            
            # Crea documento PDF
            doc = SimpleDocTemplate(
                str(export_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Prepara elementi
            elements = []
            
            # Aggiungi titolo
            elements.append(Paragraph(
                "Report Analisi Documenti",
                self.styles['CustomTitle']
            ))
            elements.append(Spacer(1, 20))
            
            if include_stats:
                # Aggiungi sezione statistiche
                elements.append(Paragraph(
                    "Statistiche e Metriche",
                    self.styles['SectionTitle']
                ))
                
                # Genera grafici
                stats_plots = await self._generate_stats_plots(results)
                for plot_path in stats_plots:
                    elements.append(Image(plot_path, width=6*inch, height=4*inch))
                    elements.append(Spacer(1, 10))
                
                # Aggiungi tabella statistiche
                stats_table = await self._create_stats_table(results)
                elements.append(stats_table)
                elements.append(Spacer(1, 20))
            
            # Aggiungi risultati ricerca
            elements.append(Paragraph(
                "Risultati Ricerca",
                self.styles['SectionTitle']
            ))
            
            results_table = await self._create_results_table(
                results,
                include_content=include_content
            )
            elements.append(results_table)
            
            # Genera PDF
            doc.build(elements)
            
            return export_path
            
        except Exception as e:
            logger.error(f"Errore nella generazione del report PDF: {str(e)}")
            raise

    async def _generate_stats_plots(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Path]:
        """
        Genera grafici statistici per il report.
        """
        try:
            plot_paths = []
            
            # Estrai dati
            docs = [r["documento"] for r in results]
            scores = [r["score"] for r in results]
            
            # Plot 1: Distribuzione tipi documento
            plt.figure(figsize=(10, 6))
            type_counts = {}
            for doc in docs:
                tipo = doc.tipo_documento.value
                type_counts[tipo] = type_counts.get(tipo, 0) + 1
            
            plt.bar(type_counts.keys(), type_counts.values())
            plt.title("Distribuzione Tipi Documento")
            plt.xticks(rotation=45)
            
            plot_path = self.plots_dir / "types_dist.png"
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            plot_paths.append(plot_path)
            
            # Plot 2: Timeline documenti
            plt.figure(figsize=(12, 6))
            dates = [doc.data_caricamento for doc in docs]
            plt.hist(dates, bins=20)
            plt.title("Timeline Documenti")
            plt.xlabel("Data")
            plt.ylabel("Numero Documenti")
            
            plot_path = self.plots_dir / "timeline.png"
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            plot_paths.append(plot_path)
            
            # Plot 3: Distribuzione score
            plt.figure(figsize=(8, 6))
            sns.histplot(scores, bins=20)
            plt.title("Distribuzione Score Rilevanza")
            plt.xlabel("Score")
            plt.ylabel("Frequenza")
            
            plot_path = self.plots_dir / "scores_dist.png"
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            plot_paths.append(plot_path)
            
            return plot_paths
            
        except Exception as e:
            logger.error(f"Errore nella generazione dei grafici: {str(e)}")
            raise

    async def _create_stats_table(
        self,
        results: List[Dict[str, Any]]
    ) -> Table:
        """
        Crea tabella con statistiche principali.
        """
        try:
            # Calcola statistiche
            docs = [r["documento"] for r in results]
            scores = [r["score"] for r in results]
            
            stats = [
                ["Metrica", "Valore"],
                ["Totale Documenti", len(docs)],
                ["Score Medio", f"{sum(scores)/len(scores):.3f}"],
                ["Score Min", f"{min(scores):.3f}"],
                ["Score Max", f"{max(scores):.3f}"]
            ]
            
            # Crea tabella
            table = Table(stats)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Errore nella creazione della tabella statistiche: {str(e)}")
            raise

    async def _create_results_table(
        self,
        results: List[Dict[str, Any]],
        include_content: bool = False
    ) -> Table:
        """
        Crea tabella con i risultati della ricerca.
        """
        try:
            # Prepara header
            headers = ["ID", "Nome File", "Tipo", "Score", "Data"]
            if include_content:
                headers.append("Contenuto")
            
            # Prepara righe
            data = [headers]
            for result in results:
                doc = result["documento"]
                row = [
                    str(doc.id),
                    doc.filename,
                    doc.tipo_documento.value,
                    f"{result['score']:.3f}",
                    doc.data_caricamento.strftime("%Y-%m-%d")
                ]
                if include_content:
                    content = doc.contenuto[:200] + "..." if doc.contenuto else ""
                    row.append(content)
                data.append(row)
            
            # Crea tabella
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Errore nella creazione della tabella risultati: {str(e)}")
            raise

    async def export_to_excel(
        self,
        results: List[Dict[str, Any]],
        include_content: bool = False
    ) -> Path:
        """
        Esporta i risultati in formato Excel.
        """
        try:
            # Prepara i dati
            data = []
            for result in results:
                doc = result["documento"]
                row = {
                    "ID": doc.id,
                    "Nome File": doc.filename,
                    "Tipo": doc.tipo_documento.value,
                    "Score": result["score"],
                    "Data Caricamento": doc.data_caricamento,
                    "Stato": doc.stato_elaborazione.value
                }
                
                # Aggiungi metadati
                if doc.metadata:
                    for key, value in doc.metadata.items():
                        if isinstance(value, (str, int, float)):
                            row[f"Metadata_{key}"] = value
                
                # Aggiungi contenuto
                if include_content and doc.contenuto:
                    row["Contenuto"] = doc.contenuto[:1000]
                    
                data.append(row)
            
            # Crea DataFrame
            df = pd.DataFrame(data)
            
            # Genera nome file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.export_dir / f"results_{timestamp}.xlsx"
            
            # Salva Excel
            df.to_excel(export_path, index=False, engine='openpyxl')
            
            return export_path
            
        except Exception as e:
            logger.error(f"Errore nell'esportazione Excel: {str(e)}")
            raise

    async def export_to_json(
        self,
        results: List[Dict[str, Any]]
    ) -> Path:
        """
        Esporta i risultati in formato JSON.
        """
        try:
            # Prepara i dati
            data = []
            for result in results:
                doc = result["documento"]
                doc_data = {
                    "id": doc.id,
                    "filename": doc.filename,
                    "tipo": doc.tipo_documento.value,
                    "score": float(result["score"]),
                    "date": {
                        "caricamento": doc.data_caricamento.isoformat(),
                        "elaborazione": doc.data_elaborazione.isoformat() if doc.data_elaborazione else None,
                        "modifica": doc.data_modifica.isoformat() if doc.data_modifica else None
                    },
                    "metadata": doc.metadata,
                    "content": doc.contenuto
                }
                data.append(doc_data)
            
            # Genera nome file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.export_dir / f"results_{timestamp}.json"
            
            # Salva JSON
            with export_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            return export_path
            
        except Exception as e:
            logger.error(f"Errore nell'esportazione JSON: {str(e)}")
            raise 