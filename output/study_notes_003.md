# 백엔드 서비스 분석과 설계 (3)

- Source: https://www.youtube.com/watch?v=Cdd9Cx9082I&t=892s
- Generated: 2026-03-03 23:50

## Study Notes

### 1. [00:00 - 02:00]

![frame 1](output/frames/frame_001.jpg)

안녕하세요. 매너코드입니다. 지난 시간에 REST API의 namespace와 SoLA를 적용해서 상영시간 생성하기 시퀀스 다이어그램을 그렸습니다 이번 시간에는 지금까지 설계에서 미흡했던 부분을 마무리하도록 하겠습니다 상영시간 생성 설계를 계속하려면 먼저 Entity를 정의해야 합니다 왜냐하면 상영시간 Entity를 정의해 놔야 생성도 할 수 있기 때문이죠 Entity가 무엇인지 간단하게 살펴보겠습니다 Entity는 ID를 부여해서 관리하는 객체를 말합니다 객체에 ID가 없으면 Value Object라고 합니다 Entity는 ID가 같으면 같은 객체입니다 Value Object는 값이 같으면 같은 객체입니다 Entity는 값이 같아도 ID가 다르면 다른 객체입니다 Entity와 Value Object에 대한 자세한 설명은 도메인 주도 설계를 참고하시기 바랍니다 저자는 에릭 에반스인데요 여러분, 놀라지 마십시오 도메인 주도 설계의 저자, 에릭 에반스를 이 자리에 직접 모셨습니다 안녕하세요 한국의 개발자 여러분 에릭 에반스입니다 Entity의 식별성을 관리하는 일은 매우 중요합니다 그러나 쓸데없이 식별성을 추가하면 시스템의 성능이 저하되고 분석 작업이 별도로 필요하며 모든 객체를 동일한 것으로 보이게 해서 모델이 혼란스러워질 수 있습니다 소프트웨어 설계는 복잡성과의 끊임없는 전투입니다 그러므로 우리는 특별하게 다뤄야 할 부분과 그렇지 않은 부분을 구분해야 합니다 그럼, 공부 열심히 하시기 바랍니다 매너 코드 최고 감사합니다 네, 에반스 님이 참 좋은 말씀 해주셨는데요 한마디로, 객체를 Entity로 관리하는 것은 신중해야 한다는 얘기입니다

### 2. [02:00 - 04:00]

![frame 2](output/frames/frame_002.jpg)

그러면 이제 Entity를 정의해 봅시다 먼저 Movie Entity입니다 Movie Entity의 속성은 대부분 도메인 전문가에게 들을 수 있습니다 제일 마지막에 있는 imageIds는 영화와 관련된 이미지 파일의 ID입니다 실제 프로젝트라면 포스터와 갤러리 등 다양한 종류의 이미지가 있겠지만 여기서는 imageIds로 단순화했습니다 Theater Entity입니다 이 다이어그램은 Gemini 2.5 pro로 그린 것입니다 MSA를 반영해서 영화 예매 시스템의 Entity를 설계하라고 했고 그 중 일부를 발췌했습니다 다이어그램을 보면 Ticket이 좌석을 특정해야 하기 때문에 Seat Entity를 참조하고 있습니다 여기서 의문은 Seat가 Entity일 필요가 있느냐는 것입니다 이 프로젝트는 영화 예매 시스템입니다 극장 관리 시스템이라면 좌석의 수리 이력 같은 것을 관리해야겠지만 영화 예매 시스템에서는 좌석을 관리하지 않습니다 그리고 고객은 좌석의 열과 번호만 알면 되는데 Ticket에 이미 좌석의 열과 번호 정보가 있습니다 그러면 Ticket이 Seat를 참조할 필요가 없지 않을까요? Seat는 왜 있는 걸까요? 영화 예매 시스템에서 Seat의 역할은 Ticket을 생성할 때 좌석 위치 정보를 제공하는 것 뿐입니다 다시 말해서 Ticket 생성에 사용되는 템플릿 같은 것입니다 Ticket을 생성하기 위해서 필요할 뿐 Seat 자체가 관리 대상은 아닌 것이죠 이런 경우 Seat는 Entity일 필요가 없습니다 단순히 Value Object여도

### 3. [04:00 - 06:00]

![frame 3](output/frames/frame_003.jpg)

Ticket을 얼마든지 생성할 수 있습니다 그래서 저는 Theater Entity를 이렇게 설계했습니다 name은 극장의 이름입니다 location 속성은 극장의 좌표인데요 location이라는 이름이 좌표를 나타내기에는 애매한 표현일 수 있습니다 그러나 요구 사항이 확장되면 location에 address나 다른 다양한 위치 정보가 추가될 수 있습니다 이름이 구체적이면 확장성이 떨어지고 반대로 애매하면 직관적이지가 않습니다 적절한 타협이 중요한 것 같습니다 seatmap 속성은 blocks과 rows로 구성된 좌석의 집합입니다 Seatmap을 좀 더 자세히 살펴보겠습니다 특별한 것은 없고 O와 X로 좌석의 존재 여부를 표시합니다 왼쪽 그림의 A 와 B 블록으로 구성된 좌석들은 오른쪽처럼 표현할 수 있습니다 Seatmap 객체는 Ticket 생성 외에도 프론트엔드에서 좌석도를 그리기 위해 사용됩니다 실제 프로젝트라면 좌석이 그려질 위치와 방향 같은 속성이 추가되겠지만 여기서는 생략했습니다 Value Object인 Seatmap을 Entity로 관리한다면 오른쪽처럼 됩니다 에릭 에반스가 객체에 ID를 부여하는 것을 조심하라고 얘기한 이유가 있습니다 ID를 부여해서 관리하면 왼쪽에 Seatmap 객체처럼 최적화를 할 수 없습니다 프론트엔드에서 좌석 정보를 빈번하게 요청할 수 있습니다 그런데 Entity 배열로 전달한다면 모두에게 큰 부담일 것입니다 Ticket과 Showtime Entity입니다 Ticket Entity의 Seat 속성은 좌석 위치를 block, row, seatNumber로 구성한 Value Object입니다 Showtime은 언제, 어디서, 무엇을 상영하는지를 나타내는

### 4. [06:00 - 08:00]

![frame 4](output/frames/frame_004.jpg)

속성을 갖고 있습니다 Ticket은 showtimeId 뿐만 아니라 movieId와 theaterId도 갖고 있습니다 movieId와 theaterId는 Showtime에 존재하는데 말입니다 데이터가 중복되는데 괜찮은 걸까요? 이 프로젝트는 마이크로서비스 구조로 설계하는 중입니다 MSA는 각 서비스가 DB를 공유하지 않습니다 그래서 Ticket에 movieId와 theaterId가 없다면 Ticket과 연결된 영화와 극장을 조회하기 위해서 ShowtimesService를 호출해야 합니다 이것은 너무 불편하고 비효율적입니다 Ticket이 Showtime을 강하게 의존하게 되는 것도 문제입니다 DB를 공유하는 모놀리식 구조에서는 테이블 조인이 가능하기 때문에 강한 정규화가 일반적입니다 그러나 MSA에서는 서비스 간 의존성과 성능 문제도 중요하게 고려해야 합니다 지금까지 정의한 Entity를 정리했습니다 앞으로 프로젝트를 진행하면서 더 많은 Entity를 정의하게 되겠지만, 지금은 이 정도면 충분한 것 같습니다 Entity를 정의했으니까 이제 기존 설계의 문제점을 살펴봅시다 상영시간 생성 설계에서 가장 우려되는 점은 상영시간 생성 요청이 동기식이라는 것입니다 첫 시간에 최상위 요구 사항을 정의하면서 극장은 4,000 개라고 했습니다 여기에 극장마다 500 개의 좌석이 있고 하루에 여덟 번씩 60일 동안 상영한다고 합시다 그러면 하나의 영화에 대해서 생성해야 하는 데이터는 상영시간이 1,920,000 개이고 티켓은 960,000,000 개입니다 이것은 시간이 오래 걸리는 작업이기 때문에

### 5. [08:00 - 10:00]

![frame 5](output/frames/frame_005.jpg)

비동기로 처리해야 합니다 그리고 생성하려는 상영시간이 충돌하는지 검사하는 기능도 추가해야 합니다 상영시간이 충돌하면 좌석이 중복 예약되는 최악의 상황이 될 수 있습니다 좌석 중복 예약 문제는 최우선 요구 사항으로 정의할 만큼 중요한 문제입니다 마지막으로 상영시간을 생성하면 티켓도 생성해야 한다고 유스케이스 다이어그램을 그렸었습니다 따라서 티켓을 생성하는 기능도 추가해야 합니다 여러모로 부족한 설계인 만큼 상영시간 생성 설계를 처음부터 다시 짚어보겠습니다 상영시간 생성이 오래 걸리는 문제는 Queue를 도입해서 해결할 수 있습니다 Queue는 입력된 작업을 순차적으로 내보내기 때문에 두 명의 사용자가 동시에 작업을 요청해도 문제가 되지 않습니다 사용자가 작업을 요청하면 ShowtimeCreationService는 작업을 Queue에 넣고 transactionId를 반환합니다 transactionId는 나중에 작업을 추적하는 데 사용합니다 ShowtimeCreationService가 dequeue로 작업을 받으면 validateRequest, bulkCreateShowtimes, bulkCreateTickets 함수를 차례대로 실행합니다 validateRequest는 상영시간 충돌을 포함해서 사용자의 요청에 문제가 없는지 검사하는 함수입니다 bulkCreateShowtimes는 상영시간을 생성하는 함수이고요 bulkCreateTickets는 티켓을 생성하는 함수입니다 validateRequest 함수를 설계하기 전에 상영시간 충돌 검사를 어떻게 하면 좋을지 생각해 봅시다 알고리즘은 간단한데요 기존에 등록된 상영시간을 가져와서 사용자가 요청한 startTimes의 시간과 비교합니다

### 6. [10:00 - 12:00]

![frame 6](output/frames/frame_006.jpg)

if 조건이 복잡해 보이지만 단순히 시작 시간과 종료 시간을 비교하는 코드입니다 이 알고리즘의 시간 복잡도는 어떻게 될까요? 중첩 루프에서 알 수 있듯이 시간 복잡도는 M*N 입니다 저 이 알고리즘 좋아했습니다 설명하기 쉽게 만들고 싶었습니다 그런데 시간 복잡도를 보니까 이건 안 되겠더라고요 예를 들어서 사용자가 사무실에서 편안하게 상영시간을 입력했는데 입력 값이 증가하면 연산량이 급격히 증가한다 개발자가 이러면 안 되는 것 아닙니까? 그러므로 알고리즘을 개선해 보도록 하겠습니다 어떻게 하면 좋을까요? 강철의 연금술사, 에드워드 엘릭은 이렇게 말했습니다 "성능 최적화는 시간과 공간의 등가교환이다" 성능을 최적화한다는 것은 처리 속도를 높이거나 메모리 사용량을 줄이는 것입니다 그러니까 우리가 쓸 수 있는 자원은 시간과 공간 이 두 가지인 것입니다 하나를 아끼려면 다른 하나를 더 써야 합니다 시간과 공간 외에 교환 가능한 자원이 하나 더 있기는 합니다 바로 두뇌입니다 상영시간을 정렬한 후에 이진 탐색으로 비교하면 공간을 더 사용하지 않아도 시간을 단축할 수 있습니다 그러나 두뇌를 사용하면 머리가 아프니까 그냥 시간과 공간을 교환하겠습니다 개선된 알고리즘입니다 사용자가 요청한 상영시간을 Set에 미리 저장합니다 그리고 기존에 등록된 상영시간이 Set에 존재하는지 확인하는 것입니다 Set 만큼 공간을 사용하지만 시간을 그 이상으로 줄일 수 있으니까 좋은 교환 같습니다 개선된 알고리즘의 시간 복잡도는 어떻게 될까요?

### 7. [12:00 - 14:00]

![frame 7](output/frames/frame_007.jpg)

언뜻 중첩 루프가 두 개나 있는 것처럼 보입니다 그러나 안쪽에 있는 루프는 시작 시간과 종료 시간을 반복하는 루프입니다 즉, 입력 시간에 비례해서 증가하거나 하지는 않는다는 뜻이죠 그래서 이 알고리즘의 시간 복잡도는 M+N으로 볼 수 있습니다 이 정도 성능이면 나쁘지 않은 것 같습니다 알고리즘을 수도 코드가 아니라 UML로 그려보면 어떨까요? 알고리즘을 이해하기 쉽게 그림으로 그리는 게 좋다고 생각하실지도 모르겠습니다 그러나 코드에 익숙한 개발자는 역시 코드가 이해하기 쉬운 것 같습니다 UML을 처음 접하면 모든 것을 다이어그램으로 표현하고 싶은 욕구가 생깁니다 그러나 UML이 만능 표현법은 아닙니다 한참 충돌 검사 알고리즘을 설명했는데요 우리는 validateRequest 함수를 설계하는 중입니다 validateRequest 함수는 대상이 되는 영화와 극장이 존재하는지 확인합니다 그리고 기존 상영시간을 가져와서 충돌하는지 검사하게 됩니다 findConflictingShowtimes 함수에 지금까지 설명한 충돌 검사 알고리즘을 구현하기만 하면 됩니다 bulkCreateShowtimes 함수는 입력된 모든 극장과 시간에 대해서 showtimes를 생성합니다 그리고 생성된 showtimes를 반환합니다 bulkCreateTickets 함수는 bulkCreateShowtimes가 반환한 showtimes를 입력 값으로 받습니다 그리고 극장에서 좌석 정보를 가져와서 Ticket을 생성합니다 지금까지 설계를 하나로 합쳐봤습니다 작아서 보기 어려울 만큼 다이어그램이 복잡한데요 ShowtimeCreationService의 기능이 너무 많은 것 같습니다

### 8. [14:00 - 16:00]

![frame 8](output/frames/frame_008.jpg)

ShowtimeCreationService가 복잡해서 리팩토링이 필요해 보입니다 여기서는 ShowtimeCreationService의 기능을 세 개의 서비스로 분산시키려고 합니다 ShowtimeCreationWorkerService는 상영시간 생성 작업을 관리하는 서비스입니다 ShowtimeBulkValidatorService는 상영시간 생성 요청을 검사하는 서비스입니다 ShowtimeBulkCreatorService는 상영시간과 Ticket을 생성하는 서비스입니다 ShowtimeCreationService의 다이어그램이 길어서 둘로 나눴습니다 이건 그 중 첫 번째인데요 대부분의 기능이 다른 서비스로 분산되면서 ShowtimeCreationService는 단순 중계자 수준으로 간단해졌습니다 여기서 searchShowtimesDto 가 눈에 띄는데요 이 프로젝트에서는 요청에 사용하는 DTO의 이름은 함수명을 그대로 사용하고 뒤에 Dto를 붙입니다 ShowtimeCreationService의 나머지 부분입니다 앞서 DTO의 이름은 호출하는 함수명 뒤에 Dto를 붙인다고 했습니다 그런데 requestShowtimeCreation 함수는 BulkCreateShowtimesDto 를 받고 있습니다 왜 searchShowtimesDto처럼 RequestShowtimeCreationDto 라고 안 했을까요? requestShowtimeCreation 함수는 요청을 전달하는 역할만 합니다 실제 요청을 처리하는 함수는 bulkCreateShowtimes 함수이기 때문입니다 ShowtimeCreationWorkerService는 transactionId를 생성하고 반환합니다 그리고 Queue에 쌓인 작업을 하나씩 실행하게 됩니다 ShowtimeCreationStatus.Waiting을 보면 화살표가 검은 점에 연결됩니다 이것은 이벤트를 발생시킨다는 의미입니다

### 9. [16:00 - 18:00]

![frame 9](output/frames/frame_009.jpg)

반대로 processNextJob은 검은 점에서 화살표가 옵니다 이것은 어딘가에서 발생한 이벤트를 수신한다는 의미입니다 ShowtimeBulkValidatorService는 하는 일이 간단한데 뒤에 Service라는 이름이 붙습니다 언제 이름에 Service를 붙여야 할까요? 이 프로젝트에서는 다른 서비스를 호출해서 필요한 작업을 스스로 할 수 있으면 Service라고 명명합니다 지금 설계에서 ShowtimeBulkValidatorService는 MoviesService와 TheatersService를 호출해서 요청을 검증하고 있습니다 그런데 만약 필요한 데이터를 호출자에게 전달받아서 작업 후 결과를 반환하는 역할이라면 Service를 붙이지 않고 단순히 ShowtimeBulkValidator라고 합니다 여기서는 ShowtimeCreationWorkerService가 MoviesService와 TheatersService를 호출해서 값을 ShowtimeBulkValidator에 전달하고 있습니다 ShowtimeBulkValidator는 시키는 일만 할 뿐 독립적으로 동작하지는 못합니다 그래서 서비스가 아닙니다 ShowtimeBulkCreatorService입니다 글자가 작으니까 빨간색 박스 부분을 확대해 보겠습니다 확대해서 보면 createShowtimes나 createTickets를 호출할 때 transactionId를 넘기고 있습니다 transactionId로 작업을 추적하고 취소하기 위해서 Showtime과 Ticket Entity에 transactionId 속성을 추가해야 합니다 transactionId를 이용한 작업 취소는 차후에 다루도록 하겠습니다 지금까지 설계를 바탕으로 서비스를 정리했습니다 각각의 서비스가 제공해야 하는 기능들이 한 눈에 보입니다

### 10. [18:00 - 19:09]

![frame 10](output/frames/frame_010.jpg)

이제 프로그래머가 각 서비스를 구현하기만 하면 됩니다 여기서 각각의 서비스는 클래스를 나타내는 것은 아닙니다 MoviesService의 경우 실제로는 MoviesController나 MoviesRepository 클래스로 구현될 것입니다 결론입니다 이번 시간에는 몇 개의 중요 Entity를 정의했습니다 그 과정에서 Seat 객체는 Ticket 생성을 위한 템플릿 같은 용도이기 때문에 Value Object로 정의했습니다 그리고 모놀리식 구조에서는 강한 정규화가 일반적이지만 MSA에서는 역 정규화도 필요하다는 것을 알았습니다 시간과 공간을 교환해서 알고리즘의 처리 속도를 향상시켰습니다 이것은 성능 최적화에서 흔히 사용되는 방식이니까 잘 기억해 두시면 좋을 것 같습니다 ShowtimeCreationService를 리팩토링 했고, 그 과정에서 몇 가지 네이밍 규칙도 정했습니다 다음 시간에는 ShowtimeCreationService의 테스트에 대해서 이야기하겠습니다 수고하셨습니다
