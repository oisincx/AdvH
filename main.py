import sqlite3


def connectDB(database):
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        return conn, cursor
    except:
        print("Failed to connect to the database!")
        return False

def makeTables(conn, cursor):
    queries = [
        "CREATE TABLE IF NOT EXISTS Publications(authorString VARCHAR(255) NOT NULL, publishDate YEAR NOT NULL, sourceTitle VARCHAR(255) NOT NULL, publisherString VARCHAR(100) NOT NULL, doiURL VARCHAR(70) NOT NULL PRIMARY KEY, pathToPDF VARCHAR(255));",
        "CREATE TABLE IF NOT EXISTS Administrators(username VARCHAR(255) NOT NULL PRIMARY KEY, password VARCHAR(255) NOT NULL);"
        ]
    for query in queries:
        try:
            cursor.execute(query)
        except:
            print("Failed to create tables")
            quit()
    conn.commit()



class Publication:
    def __init__(self, authorString, publishDate, sourceTitle, publisherString, doiURL, pathToPDF):
        self._authorString = authorString
        self._publishDate = publishDate
        self._sourceTitle = sourceTitle
        self._publisherString = publisherString
        self._doiURL = doiURL
        self._pathToPDF = pathToPDF
    def generateCitation(self):
        return f"{self.getAuthorString()} ({self.getPublishDate()}) {self.getSourceTitle()}. {self.getPublisherString()}, {self.getDoiURL()}"
    #Getters
    def getAuthorString(self):
        return self._authorString
    def getPublishDate(self):
        return self._publishDate
    def getSourceTitle(self):
        return self._sourceTitle
    def getPublisherString(self):
        return self._publisherString
    def getDoiURL(self):
        return self._doiURL
    def getPathToPDF(self):
        return self._pathToPDF
    #Setters
    def setAuthorString(self, authorString):
        self._authorString = authorString
        return True
    def setPublishDate(self, publishDate):
        self._publishDate = publishDate
    def setSourceTitle(self, sourceTitle):
        self._sourceTitle = sourceTitle
    def setPublisherString(self, publisherString):
        self._publisherString = publisherString
    def setDoiURL(self, doiURL):
        self._doiURL = doiURL
    def setPathToPDF(self, pathToPDF):
        self._pathToPDF = pathToPDF


class Administrator:
    def __init__(self, username, password):
        self._username = username.lower()
        self._password = password
    def getUsername(self):
        return self._username
    def getPassword(self):
        return self._password
    def setUsername(self, username):
        self._username = username.lower()
    def setPassword(self, password):
        self._password = password


def createAdmin(conn, cursor, admin):
    try:
        cursor.execute(f"INSERT INTO Administrators VALUES ('{admin.getUsername()}', '{admin.getPassword()}');")
        conn.commit()
    except:
        print("Database query failed!")
        return False
    return True

def insertionSort(publications):
    for index in range(1, len(publications)):
        currentValue = publications[index].getPublishDate()
        position = index
        while position > 0 and (publications[position - 1].getPublishDate() < currentValue):
            publications[position].setPublishDate(publications[position - 1].getPublishDate())
            position -= 1

        publications[position].setPublishDate(currentValue)
    return publications


def validateCredentials(username, password, conn, cursor):
    try:
        cursor.execute(f"SELECT * FROM Administrators WHERE username = '{username}' AND password = '{password}';")
        return not (len(cursor.fetchall()) == 0)
    except:
        print("Database lookup failed!")
        return False
def adminPanel(admin):
    print(f"Hello, {admin.getUsername()}")
    print("-----------------------")
    print("Admin Panel")
    print("1. Add new publication")
    print("2. Delete publication")
    print("3. Add new Administrator")
    print("4. Exit admin panel")
    print("-----------------------")
    choice = input("\n#")
    match choice:
        case '1':
            print("Adding publication")
            adminPanel(admin)
        case '2':
            print("Deleting publication")
            adminPanel(admin)
        case '3':
            print("-----------------------")
            print("Administrator Management")
            username = input("What will the new admin's username be?: ")
            password = input("What will the new admin's password be?: ")
            admin = Administrator(username, password)
            if createAdmin(conn, cursor, admin):
                print(f"Succesfully created admin with username {username}!")
            else:
                print("Failed to create admin!")
            adminPanel(admin)
        case '4':
            print("Exiting admin panel..")
        case _:
            print("Invalid input!")
            adminPanel(admin)

def loadData(path, conn, cursor):
    f = open(path, 'r')
    data = f.readlines()
    data.pop(0)
    for row in data:
        row = row.rstrip('\n')
        columns = row.split('|')
        values = ""
        for column in columns:
            values += f'"{column}"' + ','
        values = values[:-1]
        query = f"INSERT INTO Publications VALUES ({values});"
        
        print(query)
        cursor.execute(query)
        conn.commit()
    f.close()


def loadData(path, conn, cursor):
    f = open(path, 'r')
    data = f.readlines()
    data.pop(0)
    for row in data:
        row = row.rstrip('\n')
        columns = row.split('|')
        values = ""
        for column in columns:
            values += f'"{column}"' + ','
        values = values[:-1]
        query = f"INSERT INTO Publications VALUES ({values});"
        
        print(query)
        cursor.execute(query)
        conn.commit()
    f.close()

def loadPublications(conn, cursor):
    try:
        cursor.execute("SELECT * FROM Publications;")
        data = cursor.fetchall()
        publications = []
        for row in data:
            entry = Publication(row[0], row[1], row[2], row[3], row[4], row[5])
            publications.append(entry)
    except:
        print("Failed to perform database lookup!")
    return publications

def insertPublications(conn, cursor, publications):
    for publication in publications:
        values = f"{publication.getAuthorString()}, {publication.getPublishDate()}, {publication.getSourceTitle()}, {publication.getSourceTitle()}, {publication.getPublisherString()}, {publication.getDoiURL()}, {publication.getPathToPDF()}"
        query = f"INSERT INTO Publications VALUES ({values});"
        print(query)
        cursor.execute(query)
        conn.commit()
def dropPublications(conn, cursor):
    cursor.execute("DROP TABLE Publications;")
    conn.commit()

def outputPublications(publications):
    print("-----------------------")
    for index, publication in enumerate(publications):
        print(f"{index+1}. {publication.generateCitation()}")
        print("-----------------------")



def main():
    print("-----------------------")
    print("Academic Database")
    print("1. View database sorted by date published descending")
    print("2. Login as an Admin")
    print("3. Search the database by date")
    print("4. Exit the program")
    print("-----------------------")
    choice = input("\n#")
    match choice:
        case '1':
            print("Sorted database")
            publications = loadPublications(conn, cursor)
            publications = insertionSort(publications)
            outputPublications(publications)
            main()
        case '2':
            username = input("What is your username?: ")
            password = input("What is your password?: ")
            if validateCredentials(username, password, conn, cursor):
                loggedIn = Administrator(username, password)
                adminPanel(loggedIn)
            else:
                print("Incorrect credentials!")
            main()
        case '3':
            print("Database search")
            main()
        case '4':
            print("Quitting...")
            quit()
        case _:
            print("Invalid input!")
            main()


conn, cursor = connectDB('database.db')
makeTables(conn, cursor)
#publications = loadPublications(conn, cursor)
#print(publications)
#publications = insertionSort(publications)
#dropPublications(conn, cursor)
#insertPublications(conn, cursor, publications)
#loadData('exampledata.txt', conn, cursor)
main()
