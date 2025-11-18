class Node:
    """Representa um nó na Árvore Binária de Busca."""
    def __init__(self, key, data):
        self.key = key
        self.data = data
        self.left = None
        self.right = None

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
        

    def _insert_recursive(self, node, key, data):
        """Função auxiliar recursiva para inserção."""
        if key < node.key:
            if node.left is None:
                node.left = Node(key, data)
            else:
                self._insert_recursive(node.left, key, data)
        elif key > node.key:
            if node.right is None:
                node.right = Node(key, data)
            else:
                self._insert_recursive(node.right, key, data)

    def inorder_traversal(self, node):
        """
        Percorre a árvore em ordem (Inorder) para retornar os eventos
        em ordem cronológica.
        """
        res = []
        if node:
            res.extend(self.inorder_traversal(node.left))
            
            res.append({"key": node.key, "data": node.data})
            
            res.extend(self.inorder_traversal(node.right))
        return res

    def get_all_events_sorted(self):
        """Função wrapper para obter todos os eventos ordenados."""
        return self.inorder_traversal(self.root)