# Lab

**Kernel riusabile di ricerca e monitoraggio, capace di trasformare il modo
in cui continua il lavoro.** Versione 0.1.0a2, release alpha con licenza MIT.

Il Lab può affrontare questioni diverse, osservare un sistema nel tempo,
formare metodi e competenze e usarli nel campo successivo. L'Entity è il
soggetto che conserva questa continuità di significato e azione nel proprio
ambiente. La sua incarnazione dipende dal ricevente cognitivo e dai mezzi
effettivamente disponibili.

Il pacchetto comprende due forme collegate:

- **Nucleo semantico:** BOOT, KERNEL, CONCEPTS e COMPETENCES rendono operanti
  comprensione dei concetti, osservazione, autologia, formazione di capacità,
  memoria selettiva e rientro. Si usano nello spazio di lavoro dell'AI.
- **Supporto eseguibile:** Python 3.11 o successivo, senza dipendenze runtime,
  conserva fonti, contatti e occorrenze; riporta la conoscenza selezionata nel
  contesto seguente e riceve snapshot di sistemi da monitorare. Un bridge
  cognitivo scelto dal ricevente può sostenere occorrenze autonome delimitate.

L'ingresso AGENTS/BOOT partecipa alle istruzioni e all'identità del contatto,
insieme a KERNEL, CONCEPTS e COMPETENCES. Nel sorgente operano i documenti
leggibili; nella wheel le risorse corrispondenti. Una variazione rende
riconoscibile il nuovo contesto e impedisce di depositare come corrente un
evento preparato prima del cambiamento.

Il bridge ha raccolta stdout limitata durante la lettura (4 MiB di default)
e un limite distinto per stderr (64 KiB, contato senza conservarne il testo).
Superare uno dei limiti interrompe il processo diretto e registra un incidente.
Il comando mantiene i permessi dell'host: l'isolamento OS resta al ricevente.

Apri il pacchetto con il tuo ambiente AI, parti da AGENTS.md e BOOT.md e
affida il contesto al Lab. Per usare il supporto locale:

```sh
python lab.py --state ./mio-lab observe --id sistema --file examples/system.json
python lab.py --state ./mio-lab prepare --focus sistema > contatto.json
```

Il ricevente legge il contatto, forma l'occorrenza e la restituisce in JSON,
con lo stesso event_id e lo schema dnd.lab.occurrence.v1. La risultante conserva
la forma accaduta. Il comando record la riceve senza classificarne il valore
scientifico; verify controlla i digest. Il README inglese contiene comandi,
contratto del bridge e opzioni complete.

Le competenze possono conservare conoscenze, metodi, ragioni, condizioni e ciò
che può cambiarne la lettura. Ogni forma resta raggiungibile tramite available
e competence; il ricevente può selezionarla anche per un problema differente.
I risultati completi rimangono recuperabili nel deposito. La presenza di una
competenza nel contesto registra il contatto: il suo contributo effettivo si
osserva nel lavoro successivo.

Il monitor può osservare un file JSON prodotto da un sistema. Una differenza
di contenuto può rendere pertinente una nuova interpretazione. Il Lab conserva
distinti dati, unità, condizioni della raccolta e significato. Osservare un
sistema non ne autorizza automaticamente il controllo.

Questo pacchetto nasce senza dati, identità o memoria del Lab originale.
Lo stato appartiene alla directory scelta dal ricevente; le fonti private e
il laboratorio operativo mantengono la propria continuità. Il pacchetto è distribuito con [licenza MIT](LICENSE), applicata ai file di
questo repository. Le licenze delle fonti e dei repository storici restano
proprie. [Scarica la release 0.1.0a2](https://github.com/GrazianoGuiducci/dnd-lab-kernel/releases/tag/v0.1.0a2)
e leggi le [verifiche e i loro limiti](docs/VALIDATION.md).
