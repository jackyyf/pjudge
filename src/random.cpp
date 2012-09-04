#include<cstdio>
#include<cstdlib>
#include<ctime>

int main(){
	int n;
	srand(time(NULL));
	scanf("%d", &n);
	printf("%d\n", rand() % n + 1);
	return 0;
}
