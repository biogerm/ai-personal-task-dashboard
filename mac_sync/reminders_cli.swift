import Foundation
import EventKit

let store = EKEventStore()

// Extension to serialize to JSON
extension EKReminder {
    func toDictionary() -> [String: Any] {
        return [
            "id": self.calendarItemIdentifier,
            "title": self.title ?? "",
            "notes": self.notes ?? "",
            "priority": self.priority,
            "isCompleted": self.isCompleted,
            "creationDate": self.creationDate?.timeIntervalSince1970 ?? 0,
            "lastModifiedDate": self.lastModifiedDate?.timeIntervalSince1970 ?? 0,
            "dueDate": self.dueDateComponents?.date?.timeIntervalSince1970 ?? 0
        ]
    }
}

func printErrorAndExit(_ message: String) -> Never {
    fputs("\(message)\n", stderr)
    exit(1)
}

func requestAccessSync() {
    let group = DispatchGroup()
    var accessGranted = false
    
    if #available(macOS 14.0, *) {
        store.requestFullAccessToReminders { (granted, error) in
            accessGranted = granted
            group.leave()
        }
    } else {
        store.requestAccess(to: .reminder) { (granted, error) in
            accessGranted = granted
            group.leave()
        }
    }
    
    group.enter()
    group.wait()
    
    if !accessGranted {
        printErrorAndExit("Error: Reminder access not granted.")
    }
}

func getList(name: String) -> EKCalendar? {
    let calendars = store.calendars(for: .reminder)
    return calendars.first(where: { $0.title == name })
}

func fetchReminders(listName: String) {
    guard let list = getList(name: listName) else {
        printErrorAndExit("Error: List '\(listName)' not found.")
    }
    
    let predicate = store.predicateForReminders(in: [list])
    let group = DispatchGroup()
    
    group.enter()
    store.fetchReminders(matching: predicate) { reminders in
        guard let reminders = reminders else {
            print("[]")
            group.leave()
            return
        }
        
        // Filter: We only want incomplete tasks, OR tasks completed within the last 24 hours (for syncing completion).
        // AND we explicitly filter OUT any tasks that have recurrence rules.
        let now = Date()
        let filtered = reminders.filter { r in
            // Must NOT have recurrence rules
            if r.hasRecurrenceRules { return false }
            
            if !r.isCompleted { return true }
            
            // If completed, only keep if completed recently (e.g., last 7 days) to avoid returning huge history
            if let completionDate = r.completionDate, now.timeIntervalSince(completionDate) < 7 * 24 * 3600 {
                return true
            }
            return false
        }
        
        let dicts = filtered.map { $0.toDictionary() }
        if let jsonData = try? JSONSerialization.data(withJSONObject: dicts, options: .prettyPrinted),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            print(jsonString)
        } else {
            print("[]")
        }
        group.leave()
    }
    group.wait()
}

func completeReminder(id: String) {
    guard let item = store.calendarItem(withIdentifier: id) as? EKReminder else {
        printErrorAndExit("Error: Reminder with id '\(id)' not found.")
    }
    item.isCompleted = true
    do {
        try store.save(item, commit: true)
        print("{\"status\": \"success\"}")
    } catch {
        printErrorAndExit("Error saving reminder: \(error)")
    }
}

func updateReminderFull(id: String, title: String?, notes: String?, priority: Int, dueDate: Double) {
    guard let item = store.calendarItem(withIdentifier: id) as? EKReminder else {
        printErrorAndExit("Error: Reminder with id '\(id)' not found.")
    }
    
    var changed = false
    
    if let newTitle = title, item.title != newTitle {
        item.title = newTitle
        changed = true
    }
    if let newNotes = notes, item.notes != newNotes {
        item.notes = newNotes
        changed = true
    }
    if priority >= 0, item.priority != priority {
        item.priority = priority
        changed = true
    }
    if dueDate >= 0 {
        if dueDate == 0 {
            if item.dueDateComponents != nil {
                item.dueDateComponents = nil
                changed = true
            }
        } else {
            let date = Date(timeIntervalSince1970: dueDate)
            let newComps = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: date)
            if item.dueDateComponents != newComps {
                item.dueDateComponents = newComps
                changed = true
            }
        }
    }
    
    if changed {
        do {
            try store.save(item, commit: true)
            print("{\"status\": \"success\"}")
        } catch {
            printErrorAndExit("Error saving reminder: \(error)")
        }
    } else {
        print("{\"status\": \"no_change\"}")
    }
}

func main() {
    let args = CommandLine.arguments
    if args.count < 2 {
        printErrorAndExit("Usage: reminders_cli.swift <command> [args...]")
    }
    
    requestAccessSync()
    let command = args[1]
    
    switch command {
    case "fetch":
        if args.count < 3 { printErrorAndExit("Usage: fetch <listName>") }
        fetchReminders(listName: args[2])
        
    case "complete":
        if args.count < 3 { printErrorAndExit("Usage: complete <id>") }
        completeReminder(id: args[2])
        
    case "update-notes":
        if args.count < 4 { printErrorAndExit("Usage: update-notes <id> <notes>") }
        updateReminderFull(id: args[2], title: nil, notes: args[3], priority: -1, dueDate: -1)
        
    case "update-full":
        // update-full <id> <title> <notes> <priority> <dueDateTimestamp>
        if args.count < 7 { printErrorAndExit("Usage: update-full <id> <title> <notes> <priority> <dueDateTimestamp>") }
        let id = args[2]
        let title = args[3].isEmpty ? nil : args[3]
        let notes = args[4].isEmpty ? nil : args[4]
        let priority = Int(args[5]) ?? -1
        let dueDate = Double(args[6]) ?? -1
        updateReminderFull(id: id, title: title, notes: notes, priority: priority, dueDate: dueDate)
        
    default:
        printErrorAndExit("Unknown command: \(command)")
    }
}

main()
