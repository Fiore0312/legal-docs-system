from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import json
from datetime import datetime
import logging
from ..models.documento import Documento, DocumentType

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self):
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()

    async def export_to_excel(
        self,
        documenti: List[Documento],
        include_content: bool = False
    ) -> Path:
        """
        Esporta i documenti in formato Excel.
        """
        try:
            # Prepara i dati per il DataFrame
            data = []
            for doc in documenti:
                row = {
                    "ID": doc.id,
                    "Nome File": doc.filename,
                    "Tipo": doc.tipo_documento.value,
                    "Data Caricamento": doc.data_caricamento,
                    "Data Elaborazione": doc.data_elaborazione,
                    "Stato": doc.stato_elaborazione.value
                }
                
                # Aggiungi metadati se presenti
                if doc.metadata:
                    for key, value in doc.metadata.items():
                        if isinstance(value, (str, int, float)):
                            row[f"Metadata_{key}"] = value
                
                # Aggiungi contenuto se richiesto
                if include_content and doc.contenuto:
                    row["Contenuto"] = doc.contenuto[:1000]  # Limita lunghezza
                    
                data.append(row)
            
            # Crea DataFrame
            df = pd.DataFrame(data)
            
            # Genera nome file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.export_dir / f"documenti_{timestamp}.xlsx"
            
            # Salva Excel
            df.to_excel(export_path, index=False, engine='openpyxl')
            
            return export_path
            
        except Exception as e:
            logger.error(f"Errore nell'esportazione Excel: {str(e)}")
            raise

    async def generate_report(
        self,
        documenti: List[Documento],
        include_stats: bool = True
    ) -> Path:
        """
        Genera un report PDF con statistiche e tabelle.
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
            title = Paragraph(
                "Report Documenti",
                self.styles['Heading1']
            )
            elements.append(title)
            
            if include_stats:
                # Calcola statistiche
                stats = self._calculate_stats(documenti)
                
                # Aggiungi tabella statistiche
                elements.append(Paragraph("Statistiche", self.styles['Heading2']))
                stats_table = Table([
                    ["Metrica", "Valore"],
                    ["Totale Documenti", stats["total"]],
                    ["Per Tipo", ""],
                    *[[k, v] for k, v in stats["by_type"].items()],
                    ["Per Stato", ""],
                    *[[k, v] for k, v in stats["by_status"].items()]
                ])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(stats_table)
            
            # Aggiungi tabella documenti
            elements.append(Paragraph("Lista Documenti", self.styles['Heading2']))
            data = [["ID", "Nome File", "Tipo", "Stato", "Data"]]
            for doc in documenti:
                data.append([
                    str(doc.id),
                    doc.filename,
                    doc.tipo_documento.value,
                    doc.stato_elaborazione.value,
                    doc.data_caricamento.strftime("%Y-%m-%d")
                ])
            
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
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER')
            ]))
            elements.append(table)
            
            # Genera PDF
            doc.build(elements)
            
            return export_path
            
        except Exception as e:
            logger.error(f"Errore nella generazione del report: {str(e)}")
            raise

    def _calculate_stats(self, documenti: List[Documento]) -> Dict[str, Any]:
        """
        Calcola statistiche sui documenti.
        """
        stats = {
            "total": len(documenti),
            "by_type": {},
            "by_status": {}
        }
        
        # Conta per tipo
        for tipo in DocumentType:
            count = len([d for d in documenti if d.tipo_documento == tipo])
            if count > 0:
                stats["by_type"][tipo.value] = count
        
        # Conta per stato
        for doc in documenti:
            stato = doc.stato_elaborazione.value
            stats["by_status"][stato] = stats["by_status"].get(stato, 0) + 1
            
        return stats

    async def export_structured_data(
        self,
        documenti: List[Documento],
        format: str = "json"
    ) -> Path:
        """
        Esporta i dati strutturati dei documenti.
        """
        try:
            # Prepara i dati
            data = []
            for doc in documenti:
                doc_data = {
                    "id": doc.id,
                    "filename": doc.filename,
                    "tipo": doc.tipo_documento.value,
                    "stato": doc.stato_elaborazione.value,
                    "date": {
                        "caricamento": doc.data_caricamento.isoformat(),
                        "elaborazione": doc.data_elaborazione.isoformat() if doc.data_elaborazione else None,
                        "modifica": doc.data_modifica.isoformat() if doc.data_modifica else None
                    },
                    "metadata": doc.metadata
                }
                data.append(doc_data)
            
            # Genera nome file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == "json":
                export_path = self.export_dir / f"data_{timestamp}.json"
                with export_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            elif format.lower() == "csv":
                export_path = self.export_dir / f"data_{timestamp}.csv"
                df = pd.json_normalize(data)
                df.to_csv(export_path, index=False)
                
            else:
                raise ValueError(f"Formato non supportato: {format}")
                
            return export_path
            
        except Exception as e:
            logger.error(f"Errore nell'esportazione dei dati: {str(e)}")
            raise 