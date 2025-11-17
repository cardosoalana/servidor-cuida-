class Node:
    """Representa um nó na Árvore Binária de Busca."""
    def __init__(self, key, data):
        # A 'key' será o timestamp (Unix time) para ordenar cronologicamente.
        # 'data' armazena as informações do evento (lat, lon, tipo, acel).
        self.key = key
        self.data = data
        self.left = None
        self.right = None
        # Opcional: Para ABB auto-balanceável (como AVL), você adicionaria altura/balanceamento aqui.

class BinarySearchTree:
    """Implementa a lógica da Árvore Binária de Busca (ABB)."""
    def __init__(self):
        self.root = None

    def insert(self, key, data):
        """Insere um novo evento na ABB com base no timestamp (key)."""
        if self.root is None:
            self.root = Node(key, data)
        else:
            self._insert_recursive(self.root, key, data)
        
        # Para fins de teste, você pode retornar o nó raiz ou True/False

    def _insert_recursive(self, node, key, data):
        """Função auxiliar recursiva para inserção."""
        if key < node.key:
            # Vai para a subárvore esquerda
            if node.left is None:
                node.left = Node(key, data)
            else:
                self._insert_recursive(node.left, key, data)
        elif key > node.key:
            # Vai para a subárvore direita
            if node.right is None:
                node.right = Node(key, data)
            else:
                self._insert_recursive(node.right, key, data)
        # Se key == node.key, ignoramos (não deve acontecer com timestamp Unix)

    def inorder_traversal(self, node):
        """
        Percorre a árvore em ordem (Inorder) para retornar os eventos
        em ordem cronológica.
        """
        res = []
        if node:
            # 1. Visita o filho esquerdo (menores chaves/eventos mais antigos)
            res.extend(self.inorder_traversal(node.left))
            
            # 2. Visita o nó atual
            res.append({"key": node.key, "data": node.data})
            
            # 3. Visita o filho direito (maiores chaves/eventos mais recentes)
            res.extend(self.inorder_traversal(node.right))
        return res

    def get_all_events_sorted(self):
        """Função wrapper para obter todos os eventos ordenados."""
        return self.inorder_traversal(self.root)